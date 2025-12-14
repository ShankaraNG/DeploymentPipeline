import os
from datetime import datetime
import configloader as cnfloader
import configparser

def createRunConfiguration(pipelineno, Mode, Type, REPOURL, TARGETBRANCH, servername, deploy, backfilename, emaildistributionlist):
    config = cnfloader.load_properties()
    output_dir = config.get('configpathforflaskconfiguration')
    os.makedirs(output_dir, exist_ok=True)
    filename = f"runconfiguration_{pipelineno}.properties"
    filepath = os.path.join(output_dir, filename)
    config = configparser.ConfigParser()
    config.optionxform = str
    config['DEFAULT'] = {
        'Mode': Mode,
        'Type': Type,
        'REPO_URL': REPOURL,
        'TARGET_BRANCH': TARGETBRANCH,
        'servername': servername,
        'deploy': str(deploy).lower(),
        'backfilename': backfilename,
        'emaildistributionlist': emaildistributionlist
    }

    # Write configuration file
    with open(filepath, 'w') as configfile:
        config.write(configfile)
    return filepath
