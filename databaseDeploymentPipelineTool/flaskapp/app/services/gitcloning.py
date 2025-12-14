import git
from urllib.parse import quote
import os
import sys
import shutil
import stat
import subprocess
# import mailing as mailing
import services.mailing as mailing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import configloader as cnfloader
import logger as logging


def gitclone(GITLAB_USERNAME, GITLAB_TOKEN, REPO_URL, TARGET_BRANCH, CLONE_DIR, pipelineno):
    try:
        config = cnfloader.load_properties()
        encoded_username = quote(GITLAB_USERNAME)
        encoded_token = quote(GITLAB_TOKEN)
        authenticated_url = REPO_URL.replace(
            "https://", f"https://{encoded_username}:{encoded_token}@"
        )

        def onrmerror(func, path, exc_info):
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise ValueError((400, "Unable to change the permission for the path"))
        if os.path.exists(CLONE_DIR):
            logging.logger('INFO', 'GITCLONE', pipelineno, 200, "Cleaning up existing directory")
            shutil.rmtree(CLONE_DIR, onerror=onrmerror)
        else:
            parent_dir = os.path.dirname(CLONE_DIR)
            if not os.path.exists(parent_dir):
                logging.logger('INFO', 'GITCLONE', pipelineno, 200, "Creating Parent Directory")
                os.makedirs(parent_dir, exist_ok=True)
        
        logging.logger('INFO', 'GITCLONE', pipelineno, 200, f"cloning the respository {authenticated_url}")
        repo = git.Repo.clone_from(authenticated_url, CLONE_DIR)

        logging.logger('INFO', 'GITCLONE', pipelineno, 200, f"checking out the target branch {TARGET_BRANCH}")
        repo.git.fetch()
        repo.git.checkout(TARGET_BRANCH)
        logging.logger('INFO', 'GITCLONE', pipelineno, 200, "pulling the latest changes")
        repo.git.pull("origin", TARGET_BRANCH)
        logging.logger('INFO', 'GITCLONE', pipelineno, 200, "Git cloning process completed successfully")
        return "Success"
    except Exception as e:
        config = cnfloader.load_properties()
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 404, str(e)
        logging.logger('ERROR', 'GITCLONE', pipelineno, code, message)
        if code in [400, 404]:
            sendmails = config.get('Sendmail', "false").strip().upper() == "TRUE"
            if(sendmails):
                mailing.sendbatchemail(f'Pipeline has failed with the below mentioned error\n{message}', pipelineno)
            logging.applicationwriterupdate(pipelineno, 'GITCLONING', 'FAILED')
            sys.exit(1)


def gitcleanup(CLONE_DIR, pipelineno):
    try:
        config = cnfloader.load_properties()
        if os.path.exists(CLONE_DIR):
            logging.logger('INFO', 'GITCLONE', pipelineno, 200, "Cleaning up existing directory")
            try:
                repo1 = git.Repo(CLONE_DIR)
                repo1.git.reset('--hard')
                repo1.git.clean('-fdx')
            except git.InvalidGitRepositoryError:
                logging.logger('ERROR', 'GITCLONE', pipelineno, 500, f"{CLONE_DIR} is not a Git repository")
            shutil.rmtree(CLONE_DIR, onerror=lambda func, path, exc_info: os.chmod(path, stat.S_IWUSR) or func(path))
            logging.logger('INFO', 'GITCLONE', pipelineno, 200, "Cleaning up completed successfully")
        else:
            logging.logger('INFO', 'GITCLONE', pipelineno, 200, "Directory does not exist no cleanup needed")
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
            logging.applicationwriterupdate(pipelineno, 'CLEANING', 'FAILED')
            sys.exit(1)

