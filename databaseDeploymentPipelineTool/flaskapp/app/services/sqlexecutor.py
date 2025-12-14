import subprocess
import os
import sys
import stat
import tempfile
import platform
import services.mailing as mailing
# import services.mailing as mailing
# import mailing as mailing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import configloader as cnfloader
import logger as logging

def ensurefullpermissions(path, pipelineno):
    try:
        config = cnfloader.load_properties()
        if os.path.exists(path):
            os.chmod(path, stat.S_IRWXU)
        else:
            raise ValueError((400, "Source path does not exist"))
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'GITCLONE', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'PERMISSION', 'FAILED')
            sys.exit(1)

def runsqlplusscript(dbHostname, dbPort, dbServicename, dbUser, dbPassword, scriptpath, filename, sqlpluspath, pipelineno):
    try:
        config = cnfloader.load_properties()
        sqlscriptpath = os.path.join(scriptpath, filename)
        if not os.path.isfile(sqlscriptpath):
            raise FileNotFoundError((404, f"Script path does not exist  {sqlscriptpath}"))
              
        ensurefullpermissions(sqlscriptpath, pipelineno)
        # connectionString = (
        #     f"{dbUser}/{dbPassword}@"
        #     f"(DESCRIPTION="
        #     f"(ADDRESS=(PROTOCOL=TCP)(HOST={dbHostname})(PORT={dbPort}))"
        #     f"(CONNECT_DATA=(SERVICE_NAME={dbServicename}))"
        #     f")"
        # )

        connectionString = f"{dbUser}/{dbPassword}@{dbHostname}:{dbPort}/{dbServicename}"

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".sql") as tempscript:
            tempscript.write("WHENEVER SQLERROR EXIT SQL.SQLCODE;\n")
            tempscript.write("SET ECHO ON;\n")
            tempscript.write("SET DEFINE OFF;\n")
            tempscript.write(f"@{sqlscriptpath}\n")
            tempscript.write("EXIT;\n")
            tempscriptpath = tempscript.name
        
        os.chmod(tempscriptpath, stat.S_IRWXU)

        sqlpluscmd = f'"{sqlpluspath}"' if ' ' in sqlpluspath else sqlpluspath
        command = f'{sqlpluscmd} -s {connectionString} @{tempscriptpath}'        
        logging.logger('INFO', 'SQLEXECUTOR', pipelineno, 200, f"Executing SQL script: {sqlscriptpath}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if os.path.exists(tempscriptpath):
            os.unlink(tempscriptpath)

        # os.unlink(tempscriptpath)

        if result.returncode != 0:
            raise ValueError((600, f"SQL*Plus failed with exit code {result.returncode}\n{result.stdout}\n{result.stderr}"))
        
        logging.logger('INFO', 'SQLEXECUTOR', pipelineno, 200, f"SQL script {filename} executed successfully")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'SQLEXECUTOR', pipelineno, code, message)
        if code in [400, 404, 600]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'SQLDEPLOYMENT', 'FAILED')
            sys.exit(1)
        return None
