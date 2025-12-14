import os
import sys
import shutil
import stat
import services.mailing as mailing
# import services.mailing as mailing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config_loader as cnfloader
import logger as logging

def ensurefullpermissions(path, pipelineno):
    try:
        config = cnfloader.load_properties()
        if os.path.exists(path):
            os.chmod(path, stat.S_IRWXU)  # Read, write, execute for user
        else:
            raise ValueError((400, "Source path does not exist"))
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'FILESMOVER', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'PERMISSION', 'FAILED')
            sys.exit(1)


def filemove(source, filedirectoryname, subdirectory, filename, targetdirectory, pipelineno):
    try:
        config = cnfloader.load_properties()
        sourcedirectory = os.path.join(source, filedirectoryname, subdirectory)
        sourcefile = os.path.join(sourcedirectory, filename)
        if not os.path.exists(sourcedirectory):
            raise ValueError((400, f"Source directory {sourcedirectory} does not exist"))
        if not os.path.exists(sourcefile):
            raise ValueError((400, f"Source file {sourcefile} does not exist"))
        ensurefullpermissions(sourcedirectory, pipelineno)
        ensurefullpermissions(sourcefile, pipelineno)

        if not os.path.exists(targetdirectory):
            logging.logger('INFO', 'FILEMOVE', pipelineno, 200, f"Creating target directory {targetdirectory}")
            os.makedirs(targetdirectory, exist_ok=True)
        
        ensurefullpermissions(targetdirectory, pipelineno)
        destinationfile = os.path.join(targetdirectory, filename)
        
        if os.path.exists(destinationfile):
            logging.logger('INFO', 'FILEMOVE', pipelineno, 200, f"Replacing existing file {destinationfile}")
            ensurefullpermissions(destinationfile, pipelineno)
            os.remove(destinationfile)

        shutil.copy2(sourcefile, destinationfile)
        logging.logger('INFO', 'FILEMOVE', pipelineno, 200, f"File {filename} moved successfully to {targetdirectory}")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'FILEMOVE', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'FILESMOVE', 'FAILED')
            sys.exit(1)
        return None


def filecheck(source, filedirectoryname, subdirectory, filename, pipelineno):
    try:
        config = cnfloader.load_properties()
        sourcedirectory = os.path.join(source, filedirectoryname, subdirectory)
        sourcefile = os.path.join(sourcedirectory, filename)
        if not os.path.exists(sourcedirectory):
            raise ValueError((400, f"Source directory {sourcedirectory} does not exist"))
        if not os.path.exists(sourcefile):
            raise ValueError((400, f"Source file {sourcefile} does not exist"))
        ensurefullpermissions(sourcedirectory, pipelineno)
        ensurefullpermissions(sourcefile, pipelineno)
        logging.logger('INFO', 'FILECHECK', pipelineno, 200, f"File {filename} Exists in the source directory")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'FILECHECK', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'FILESCHECK', 'FAILED')
            sys.exit(1)
        return None
    
def fileinitialbackup(backuppath, filedirectoryname, subdirectory, filename, targetdirectory, pipelineno):
    try:
        config = cnfloader.load_properties()
        backupdirectory = os.path.join(backuppath, filedirectoryname, subdirectory)
        backupfile = os.path.join(backupdirectory, filename)
        if not os.path.exists(backupdirectory):
            os.makedirs(backupdirectory, exist_ok=True)
        ensurefullpermissions(backupdirectory, pipelineno)
        if not os.path.exists(targetdirectory):
            logging.logger('INFO', 'BACKUPJOB', pipelineno, 200, f"The directory does not exist in the path {targetdirectory}")
            return "Success"
        else:
            ensurefullpermissions(targetdirectory, pipelineno)
        
        originalfile = os.path.join(targetdirectory, filename)
        if not os.path.exists(originalfile):
            logging.logger('INFO', 'BACKUPJOB', pipelineno, 200, f"File does not exists in the directory {originalfile}")
            return "Success"
        else:
            ensurefullpermissions(originalfile, pipelineno)
            shutil.copy2(originalfile, backupfile)
            logging.logger('INFO', 'BACKUPJOB', 200, f"File {filename} Backed up successfully")
            return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'FILEMOVE', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'FILESBACKUP', 'FAILED')
            sys.exit(1)
        return None
    

def filerollback(backuppath, filedirectoryname, subdirectory, filename, targetdirectory, pipelineno):
    try:
        config = cnfloader.load_properties()
        backupdirectory = os.path.join(backuppath, filedirectoryname, subdirectory)
        backupfile = os.path.join(backupdirectory, filename)
        if not os.path.exists(backupdirectory):
            raise ValueError((404, f"Backed up file directory {backupdirectory} does not exist"))
        if not os.path.exists(backupfile):
            raise ValueError((404, f"Backup file {backupfile} does not exist"))
        ensurefullpermissions(backupdirectory, pipelineno)
        ensurefullpermissions(backupfile, pipelineno)
        if not os.path.exists(targetdirectory):
            os.makedirs(targetdirectory, exist_ok=True)        
        ensurefullpermissions(targetdirectory, pipelineno)        
        rollbackfile = os.path.join(targetdirectory, filename)
        if not os.path.exists(rollbackfile):
            logging.logger('INFO', 'BACKUPJOB', pipelineno, 200, f"File does not exists in the directory {rollbackfile}")
        else:
            logging.logger('INFO', 'BACKUPJOB', pipelineno, 200, f"Replacing existing file {rollbackfile}")
            ensurefullpermissions(rollbackfile, pipelineno)

        shutil.copy2(backupfile, rollbackfile)
        logging.logger('INFO', 'BACKUPJOB', pipelineno, 200, f"File {filename} has been rolled back successfully")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        logging.logger('ERROR', 'BACKUPJOB', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'FILEROLLBACK', 'FAILED')
            sys.exit(1)
        return None