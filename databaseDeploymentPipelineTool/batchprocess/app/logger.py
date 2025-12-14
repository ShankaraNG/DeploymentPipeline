# '{date} INFO [batchLoader] 200 Saids and province Codes fetched successfully'.format(date=datetime.now().strftime('%d %B %Y %H:%M:%S,%f')[:-3])
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config_loader as cnfloader


def logger(information, type, pipelineload, exceptioncode, data):
    try:
        config = cnfloader.load_properties()
        logfile = config.get('loggingFilePath')
        logfilename = f'scheduled_pipeline_{pipelineload}.log'
        fullloggingpath = os.path.join(logfile,logfilename)
        if not os.path.exists(fullloggingpath):
            raise ValueError("Unable to find the log path")
        pipeline = f'SCHEDULED_{pipelineload}'
        log = '{date} {information} [{type}] [{pipeline}] {exceptioncode} {data}'.format(date=datetime.now().strftime('%d %B %Y %H:%M:%S,%f')[:-3],information = information, type= type, exceptioncode = exceptioncode, data = data, pipeline=pipeline)
        print(log) 
        with open(fullloggingpath, 'a', encoding='utf-8') as f:
            f.write(log + '\n')
    except Exception as e:
        print(e)
        sys.exit(1)

def startinglogger(data, pipelineload):
    try:
        print(data)
        config = cnfloader.load_properties()
        logfile = config.get('loggingFilePath')
        logfilename = f'pipeline_{pipelineload}.log'
        fullloggingpath = os.path.join(logfile,logfilename)
        if not os.path.exists(logfile):
            os.makedirs(logfile, exist_ok=True)
        if not os.path.exists(fullloggingpath):
            with open(fullloggingpath, "w", encoding="utf-8"):
                pass
        with open(fullloggingpath, 'a', encoding='utf-8') as f:
            f.write(data + '\n')
    except Exception as e:
        print(e)
        sys.exit(1)


def applicationwriterfirst(GitUrl,Branch, Mode, Type, stage, status, pipelineload):
    try:
        config = cnfloader.load_properties()
        logfile = config.get('loggingFilePath')
        logfilename = f'pipeline_{pipelineload}.log'
        fullloggingpath = os.path.join(logfile,logfilename)
        if not os.path.exists(fullloggingpath):
            raise ValueError("Unable to find the log path") 
        time = datetime.now().strftime('%d/%m/%Y %H:%M:%S:%f')[:-3]
        line = f"{pipelineload}|{time}|{time}|{GitUrl}|{Branch}|{Mode}|{Type}|Scheduled_{pipelineload}|{stage}|{status}|{fullloggingpath}"
        writingfile = config.get('flaskHistoryDataPath')

        if not os.path.exists(writingfile):
            header = 'Pipelineno|StartTime|LastUpdatedTime|GitUrl|Branch|Deployment Mode|Deployment Type|Triggered By|Stage|Status|Logs'
            with open(writingfile, "w", encoding="utf-8"):
                f.write(header + '\n')
        with open(writingfile, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception as e:
        print(e)
        sys.exit(1)


def applicationwriterupdate(pipelineno, new_stage, new_status):
    try:
        config = cnfloader.load_properties()
        writingfile = config.get('flaskHistoryDataPath')
        if not os.path.exists(writingfile):
            raise ValueError("Unable to find the log path")
        updated_lines = []
        updated = False
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S:%f')[:-3]
        with open(writingfile, "r") as f:
            lines = f.readlines()
        header = lines[0].strip()
        updated_lines.append(header + "\n")
        for line in lines[1:]:
            parts = line.strip().split("|")
            if len(parts) < 10:
                continue
            if str(parts[0]) == str(pipelineno):
                parts[2] = now
                parts[8] = new_stage            
                parts[9] = new_status
                updated = True
            updated_lines.append("|".join(parts) + "\n")
        if updated:
            with open(writingfile, "w") as f:
                f.writelines(updated_lines)
    except Exception as e:
        print(e)
        sys.exit(1)


def loadnoupdate():
    try:
        config = cnfloader.load_properties()
        loadnofile = config.get('pipelineloadfile')
        if not loadnofile:
            raise ValueError((400, 'No File Path Found'))
        with open(loadnofile, 'r') as file:
            LoadNos = file.read().strip()
            
        if LoadNos and LoadNos.isdigit():
            LoadNo = int(LoadNos)
            LoadNo = LoadNo + 1
            with open(loadnofile, 'w') as file:
                file.write(str(LoadNo))

            return LoadNo
        else:
            print("hello")
            raise ValueError((400, 'No Load No Found'))
    except Exception as e:
        print(e)
        return None
