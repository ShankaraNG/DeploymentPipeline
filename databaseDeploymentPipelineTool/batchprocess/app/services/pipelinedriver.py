import pandas as pd
from urllib.parse import quote
from datetime import datetime
import os
import sys
import shutil
import stat
import subprocess
import services.pipelineintro as pipelineintro
import services.filemover as filemover
import services.sqlexecutor as sqlexecutor
import services.gitcloning as gitcloning
import services.mailing as mailing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config_loader as cnfloader
import logger as logging


def ensurefullpermissions(path, pipelineno):
    config = cnfloader.load_properties()
    try:
        if os.path.exists(path):
            os.chmod(path, stat.S_IRWXU)
        else:
            raise ValueError((400, "Source path does not exist"))
    except Exception as e:
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'PIPELINE', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'PERMISSION', 'FAILED')
            sys.exit(1)


def deploymentdriverforfilemove(clonedir, filesdname, configmapserver, pipelineno):
    try:
        config = cnfloader.load_properties()
        pathforfilemoveproperties = os.path.join(clonedir, 'configmap', configmapserver, 'filesmove.properties')
        if not os.path.exists(pathforfilemoveproperties):
            raise FileNotFoundError((404, f"Configuration file {pathforfilemoveproperties} does not exist"))
        ensurefullpermissions(pathforfilemoveproperties, pipelineno)
        filesmovedata_df = pd.read_csv(pathforfilemoveproperties, delimiter='|')
        backuppathtemp = config.get('backupDirectory')
        backuptempdirectory = "backupfile"+datetime.now().strftime('_%d_%m_%Y_%H_%M_%S_%f')[:-3]
        backuppath = os.path.join(backuppathtemp, backuptempdirectory)
        if not os.path.exists(backuppath):
            logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"Creating backup directory {backuppath}")
            os.makedirs(backuppath, exist_ok=True)
        ensurefullpermissions(backuppath, pipelineno)
        filedirectoryname = str(filesdname)
        for i in range(len(filesmovedata_df)):
            row = filesmovedata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            targetfolder = row[2]
            result = filemover.fileinitialbackup(backuppath, filedirectoryname, subdirectory, filename, targetfolder, pipelineno)
            if result != "Success":
                raise ValueError((500, f"File initial backup failed for {filename}"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Back up process has been compeleted")
        gitsourcedirectory = config.get('filegitdirectoryname')
        source = os.path.join(clonedir, gitsourcedirectory)
        filedirectoryname = str(filesdname)
        for i in range(len(filesmovedata_df)):
            row = filesmovedata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            result = filemover.filecheck(source, filedirectoryname, subdirectory, filename, pipelineno)
            if result != "Success":
                raise ValueError((404, f"File check failed {filename} please check if this file exists in the git repository"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "File check completed successfully")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Proceeding with deploying the files")
        gitsourcedirectory = config.get('filegitdirectoryname')
        source = os.path.join(clonedir, gitsourcedirectory)
        filedirectoryname = str(filesdname)
        for i in range(len(filesmovedata_df)):
            row = filesmovedata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            targetfolder = row[2]
            result = filemover.filemove(source, filedirectoryname, subdirectory, filename, targetfolder, pipelineno)
            if result != "Success":
                raise ValueError((404, f"File check failed {filename} please check if this file exists in the git repository"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "All files have been deployed successfully")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'PIPELINERUNNER', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'FILESMOVE', 'FAILED')
            sys.exit(1)
        return None

def deploymentdriverforsqlscript(clonedir, sqldname, configmapserver, pipelineno):
    try:
        config = cnfloader.load_properties()
        pathforsqlfileproperties = os.path.join(clonedir, 'configmap', configmapserver, 'sqlfiles.properties')
        if not os.path.exists(pathforsqlfileproperties):
            raise FileNotFoundError((404, f"Configuration file {pathforsqlfileproperties} does not exist"))
        ensurefullpermissions(pathforsqlfileproperties, pipelineno)
        sqlfilesdata_df = pd.read_csv(pathforsqlfileproperties, delimiter='|')
        sqlpluspath = config.get('sqlpluspath')
        if not sqlpluspath:
            raise ValueError((404, "Configuration parameter 'sqlpluspath' is missing"))
        gitsourcedirectory = config.get('filegitdirectoryname')
        if not gitsourcedirectory:
            raise ValueError((404, "Configuration parameter 'filegitdirectoryname' is missing"))
        source = os.path.join(clonedir, gitsourcedirectory)
        if not os.path.exists(source):
            raise FileNotFoundError((404, f"Source directory {source} does not exist"))
        ensurefullpermissions(source, pipelineno)
        filedirectoryname = str(sqldname)
        sqlscriptdirectory = os.path.join(source, filedirectoryname)
        if not os.path.exists(sqlscriptdirectory):
            raise FileNotFoundError((404, f"SQL script directory {sqlscriptdirectory} does not exist"))
        ensurefullpermissions(sqlscriptdirectory, pipelineno)
        for i in range(len(sqlfilesdata_df)):
            row = sqlfilesdata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            result = filemover.filecheck(source, filedirectoryname, subdirectory, filename, pipelineno)
            if result != "Success":
                raise ValueError((404, f"File check failed {filename} please check if this file exists in the git repository"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL file checks have been completed successfully and all files are present")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the SQL script execution process")
        for i in range(len(sqlfilesdata_df)):
            row = sqlfilesdata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            dbHostname = row[2]
            dbPort = row[3]
            dbServicename = row[4]
            dbUser = row[5]
            dbPassword = row[6]
            scriptpath = os.path.join(sqlscriptdirectory, subdirectory)
            if not os.path.exists(scriptpath):
                raise FileNotFoundError((404, f"Script path {scriptpath} does not exist"))
            ensurefullpermissions(scriptpath, pipelineno)
            result = sqlexecutor.runsqlplusscript(dbHostname, dbPort, dbServicename, dbUser, dbPassword, scriptpath, filename, sqlpluspath, pipelineno)
            if result != "Success":
                raise ValueError((404, f"File check failed {filename} please check if this file exists in the git repository"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL Scripts Execution has been completed successfully")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'PIPELINERUNNER', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'SQLDEPLOYMENT', 'FAILED')
            sys.exit(1)
        return None
        



def rollbackdriverforfilemove(clonedir, filesdname, configmapserver, pipelineno):
    try:
        config = cnfloader.load_properties()
        pathforfilemoveproperties = os.path.join(clonedir, 'configmap', configmapserver, 'filesmove.properties')
        if not os.path.exists(pathforfilemoveproperties):
            raise FileNotFoundError((404, f"Configuration file {pathforfilemoveproperties} does not exist"))
        ensurefullpermissions(pathforfilemoveproperties, pipelineno)
        filesmovedata_df = pd.read_csv(pathforfilemoveproperties, delimiter='|')
        backeupdirectorypath = config.get('backupDirectory')
        backedupdirectoryname = config.get('backfilename')
        backeduppath = os.path.join(backeupdirectorypath, backedupdirectoryname)
        if not os.path.exists(backeduppath):
            raise FileNotFoundError((404, f"Backup directory {backeduppath} does not exist"))
        ensurefullpermissions(backeduppath, pipelineno)
        fullpath = os.path.join(backeduppath, filesdname)
        if not os.path.exists(fullpath):
            raise FileNotFoundError((404, f"Full path {fullpath} does not exist"))
        ensurefullpermissions(fullpath, pipelineno)
        for i in range(len(filesmovedata_df)):
            row = filesmovedata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            targetfolder = row[2]
            result = filemover.filerollback(backeduppath, filesdname, subdirectory, filename, targetfolder, pipelineno)
            if result != "Success":
                raise ValueError((500, f"File roll back failed for {filename}"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Files Roll Back Process has been completed successfully")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'PIPELINERUNNER', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'FILEROLLBACK', 'FAILED')
            sys.exit(1)
        return None
    

def rollbackdriverforsqlscript(clonedir, sqldname, configmapserver, pipelineno):
    try:
        config = cnfloader.load_properties()
        pathforsqlfileproperties = os.path.join(clonedir, 'configmap', configmapserver, 'sqlrollbackfiles.properties')
        if not os.path.exists(pathforsqlfileproperties):
            raise FileNotFoundError((404, f"Configuration file {pathforsqlfileproperties} does not exist"))
        ensurefullpermissions(pathforsqlfileproperties, pipelineno)
        sqlfilesdata_df = pd.read_csv(pathforsqlfileproperties, delimiter='|')
        sqlpluspath = config.get('sqlpluspath')
        if not sqlpluspath:
            raise ValueError((404, "Configuration parameter 'sqlpluspath' is missing"))
        gitsourcedirectory = config.get('filegitdirectoryname')
        if not gitsourcedirectory:
            raise ValueError((404, "Configuration parameter 'filegitdirectoryname' is missing"))
        source = os.path.join(clonedir, gitsourcedirectory)
        if not os.path.exists(source):
            raise FileNotFoundError((404, f"Source directory {source} does not exist"))
        ensurefullpermissions(source, pipelineno)
        filedirectoryname = str(sqldname)
        sqlscriptdirectory = os.path.join(source, filedirectoryname)
        if not os.path.exists(sqlscriptdirectory):
            raise FileNotFoundError((404, f"SQL script directory {sqlscriptdirectory} does not exist"))
        ensurefullpermissions(sqlscriptdirectory, pipelineno)
        for i in range(len(sqlfilesdata_df)):
            row = sqlfilesdata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            result = filemover.filecheck(source, filedirectoryname, subdirectory, filename, pipelineno)
            if result != "Success":
                raise ValueError((404, f"File check failed {filename} please check if this file exists in the git repository"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL file checks have been completed successfully and all files are present")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the SQL Backout script execution process")
        for i in range(len(sqlfilesdata_df)):
            row = sqlfilesdata_df.iloc[i]
            filename = row[0]
            subdirectory = row[1]
            dbHostname = row[2]
            dbPort = row[3]
            dbServicename = row[4]
            dbUser = row[5]
            dbPassword = row[6]
            scriptpath = os.path.join(sqlscriptdirectory, subdirectory)
            if not os.path.exists(scriptpath):
                raise FileNotFoundError((404, f"Script path {scriptpath} does not exist"))
            ensurefullpermissions(scriptpath, pipelineno)
            result = sqlexecutor.runsqlplusscript(dbHostname, dbPort, dbServicename, dbUser, dbPassword, scriptpath, filename, sqlpluspath, pipelineno)
            if result != "Success":
                raise ValueError((404, f"File check failed {filename} please check if this file exists in the git repository"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL Backout Scripts Execution has been completed successfully")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'PIPELINERUNNER', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'SQLROLLBACKDEPLOYMENT', 'FAILED')
            sys.exit(1)
        return None


def pipelinerunner():
    pipelineno = None
    try:
        startingmessage = pipelineintro.intro()
        logging.startinglogger(startingmessage)
        pipelineno = logging.loadnoupdate()
        if not pipelineno:
            raise ValueError((404, f"Did not find the load number"))
        config = cnfloader.load_properties()
        gitlabusername = config.get('GITLAB_USERNAME')
        gitlabtoken = config.get('GITLAB_TOKEN')
        repourl = config.get('REPO_URL')
        targetbranch = config.get('TARGET_BRANCH')
        clonedir = config.get('CLONE_DIR')
        Mode = config.get('MODE').strip().upper()
        Type = config.get('TYPE').strip().upper()
        if(not gitlabusername or not gitlabtoken or not repourl or not targetbranch or not clonedir):
            raise ValueError((404, "One or more required configuration parameters are missing"))
        logging.applicationwriterfirst(repourl, targetbranch, Mode, Type, "STARTING", "RUNNING", pipelineno)
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting a new Pipeline run")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"Pipeline No: {pipelineno}")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"Pipeline Mode: {Mode}")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"Pipeline Type: {Type}")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Below is the configuration used for the pipeline run")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"GITLAB USERNAME: {gitlabusername}")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"REPOSITORY URL: {repourl}")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"TARGET BRANCH: {targetbranch}")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, f"CLONE DIRECTORY: {clonedir}")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Cleaning up the clone directory if it exists")
        logging.applicationwriterupdate(pipelineno, 'CLEANING', 'RUNNING')
        gitcloning.gitcleanup(clonedir, pipelineno)
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Cleaning up completed proceeding to clone the directory")
        logging.applicationwriterupdate(pipelineno, 'GITCLONING', 'RUNNING')
        resultofcloning = gitcloning.gitclone(gitlabusername, gitlabtoken, repourl, targetbranch, clonedir, pipelineno)
        if resultofcloning != "Success":
            raise ValueError((400, f"Failed in Git Cloning"))
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Git cloning completed successfully")
        logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Taking the Backup of the deployment files")
        configmapserver = config.get('servername')
        if not configmapserver:
            raise ValueError((404, "Configuration parameter 'servername' is missing"))
        if( Mode == "DEPLOY" ):
            if(Type == "FILESMOVE"):
                filesdname = config.get('filesmovegitdirectoryname')
                if not filesdname:
                    raise ValueError((404, "Configuration parameter 'filesmovegitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the Files Deployment process")
                logging.applicationwriterupdate(pipelineno, 'FILESMOVE', 'RUNNING')
                result = deploymentdriverforfilemove(clonedir, filesdname, configmapserver, pipelineno)
                if result != "Success":
                    raise ValueError((404, "File move deployment failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Files Deployment completed successfully")
                return "Success", pipelineno
            elif(Type == "SQLSCRIPTEXECUTION"):
                sqldname = config.get('sqlscriptgitdirectoryname')
                if not sqldname:
                    raise ValueError((404, "Configuration parameter 'sqlscriptgitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the SQL Script Execution Deployment process")
                logging.applicationwriterupdate(pipelineno, 'SQLEXECUTION', 'RUNNING')
                result = deploymentdriverforsqlscript(clonedir, sqldname, configmapserver, pipelineno)
                if result != "Success":
                    raise ValueError((404, "SQL script execution deployment failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL Script Execution Deployment completed successfully")
                return "Success", pipelineno
            elif(Type == "BOTH"):
                filesdname = config.get('filesmovegitdirectoryname')
                if not filesdname:
                    raise ValueError((404, "Configuration parameter 'filesmovegitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the Files Deployment process")
                logging.applicationwriterupdate(pipelineno, 'FILESMOVE', 'RUNNING')
                result = deploymentdriverforfilemove(clonedir, filesdname, configmapserver, pipelineno)
                if result != "Success":
                    raise ValueError((404, "File move deployment failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Files Deployment completed successfully")
                sqldname = config.get('sqlscriptgitdirectoryname')
                if not sqldname:
                    raise ValueError((404, "Configuration parameter 'sqlscriptgitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the SQL Script Execution Deployment process")
                logging.applicationwriterupdate(pipelineno, 'SQLEXECUTION', 'RUNNING')
                result = deploymentdriverforsqlscript(clonedir, sqldname, configmapserver, pipelineno)
                if result != "Success":
                    raise ValueError((404, "SQL script execution deployment failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL Script Execution Deployment completed successfully")
                return "Success", pipelineno
            else:
                raise ValueError((404, f"Invalid TYPE: {Type}. Expected 'FILESMOVE', 'SQLSCRIPTEXECUTION', or 'BOTH'"))
        elif( Mode == "ROLLBACK" ):
            if(Type == "FILESMOVE"):
                filesdname = config.get('filesmovegitdirectoryname')
                if not filesdname:
                    raise ValueError((404, "Configuration parameter 'filesmovegitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the Files RollBack process")
                logging.applicationwriterupdate(pipelineno, 'FILESMOVE', 'RUNNING')
                result = rollbackdriverforfilemove(clonedir, filesdname, configmapserver, pipelineno)
                if result != "Success":
                    raise ValueError((404, "File move RollBack failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Files RollBack completed successfully")
                return "Success", pipelineno
            elif(Type == "SQLSCRIPTEXECUTION"):
                sqldname = config.get('sqlrollbackgitdirectoryname')
                if not sqldname:
                    raise ValueError((404, "Configuration parameter 'sqlscriptgitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the SQL Rollback Script Execution Deployment process")
                logging.applicationwriterupdate(pipelineno, 'SQLEXECUTION', 'RUNNING')
                result = rollbackdriverforsqlscript(clonedir, sqldname, configmapserver, pipelineno)
                if result != "Success":
                    raise ValueError((404, "SQL script execution deployment failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL Rollback Script Execution Deployment completed successfully")
                return "Success", pipelineno
            elif(Type == "BOTH"):
                filesdname = config.get('filesmovegitdirectoryname')
                if not filesdname:
                    raise ValueError((404, "Configuration parameter 'filesmovegitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the Files RollBack process")
                logging.applicationwriterupdate(pipelineno, 'FILESMOVE', 'RUNNING')
                result = rollbackdriverforfilemove(clonedir, filesdname, configmapserver, pipelineno)
                if result != "Success":
                    raise ValueError((404, "File move RollBack failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Files RollBack completed successfully")
                sqldname = config.get('sqlrollbackgitdirectoryname')
                if not sqldname:
                    raise ValueError((404, "Configuration parameter 'sqlscriptgitdirectoryname' is missing"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Starting the SQL Rollback Script Execution Deployment process")
                logging.applicationwriterupdate(pipelineno, 'SQLEXECUTION', 'RUNNING')
                result = rollbackdriverforsqlscript(clonedir, sqldname, configmapserver, pipelineno)
                if result != "Success":
                    logging.applicationwriterupdate(pipelineno, 'SQLEXECUTION', 'FAILED')
                    raise ValueError((404, "SQL script execution deployment failed"))
                logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "SQL Rollback Script Execution Deployment completed successfully")
                return "Success", pipelineno
            else:
                raise ValueError((404, f"Invalid TYPE: {Type}. Expected 'FILESMOVE', 'SQLSCRIPTEXECUTION', or 'BOTH'"))
        else:
            raise ValueError((404, f"Invalid MODE: {Mode}. Expected 'DEPLOY' or 'ROLLBACK'"))                
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        if pipelineno is None:
            pipelineno = 500
        logging.logger('ERROR', 'PIPELINERUNNER', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'PIPELINERUNNER', 'FAILED')
            sys.exit(1)
        return None, pipelineno
    

def pipelinedriver():
    pipelineno = None
    try:
        config = cnfloader.load_properties()
        sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
        result, pipelineno = pipelinerunner()
        if(sendmails):
            mailing.sendbatchemail('Starting a new pipeline run', pipelineno)
        if result == "Success":
            clonedir = config.get('CLONE_DIR')
            logging.applicationwriterupdate(pipelineno, 'END', 'COMPLETED')
            logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Cleaning up the git directory")
            gitcloning.gitcleanup(clonedir, pipelineno)
            logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Clean up has been compeleted successfully")
            logging.logger('INFO', 'PIPELINERUNNER', pipelineno, 200, "Pipeline run completed successfully")
            mailing.sendbatchemail('Pipeline run completed successfully', pipelineno)
        else:
            logging.logger('ERROR', 'PIPELINERUNNER', pipelineno, 500, "Pipeline run failed")
            mailing.sendbatchemail('Pipeline has failed', pipelineno)
            return None
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        if not pipelineno:
            pipelineno = 500
        logging.logger('ERROR', 'PIPELINERUNNER', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'PIPELINERUNNER', 'FAILED')
            sys.exit(1)
        return None