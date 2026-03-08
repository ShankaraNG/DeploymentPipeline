@echo off
REM ############################################################################################################
REM ##                                 Database Deployment Pipeline                                           ##
REM ##                                                                                                        ##
REM ## This Script is developed by Shankar N G                                                                ##
REM ## It is to trigger the Flask Application of the Database Deployment Pipeline                             ##
REM ## The Flask App provides the web interface to manage and trigger the deployment pipeline                  ##
REM ## Please edit the APP_DIR path to point to where the application is installed                            ##
REM ## Make sure the virtual environment and requirements are set up before running                            ##
REM ## This Script is for Windows Command Prompt / Task Scheduler                                             ##
REM ############################################################################################################

SET APP_DIR=E:\PythonProjects\databaseDeploymentPipelineTool\flaskapp\app
SET LOG_DIR=%APP_DIR%\logs

IF NOT EXIST "%LOG_DIR%" mkdir "%LOG_DIR%"

FOR /F "tokens=1-6 delims=/:. " %%A IN ("%DATE% %TIME%") DO (
    SET LOG_FILE=%LOG_DIR%\flaskapp_%%C%%B%%A_%%D%%E%%F.log
)

echo ==============================================
echo   Starting Database Deployment Pipeline
echo   Component  : Flask Web Application
echo   Started at : %DATE% %TIME%
echo   Logs       : %LOG_FILE%
echo ==============================================

IF NOT EXIST "%APP_DIR%\flaskapp\app" (
    echo ERROR: Flask app directory not found: %APP_DIR%\flaskapp\app
    pause
    exit /b 1
)
cd /d "%APP_DIR%\flaskapp\app"

IF EXIST "%APP_DIR%\.venv\Scripts\activate.bat" (
    call "%APP_DIR%\.venv\Scripts\activate.bat"
    echo Virtual environment activated.
) ELSE (
    echo WARNING: Virtual environment not found. Running with system Python.
)

START "DeploymentPipeline-FlaskApp" /B python -m main >> "%LOG_FILE%" 2>&1

echo ==============================================
echo   Flask App is running in the background
echo   To stop: End python.exe in Task Manager
echo   Logs: %LOG_FILE%
echo ==============================================

IF EXIST "%APP_DIR%\.venv\Scripts\deactivate.bat" (
    call "%APP_DIR%\.venv\Scripts\deactivate.bat"
)

pause
