#!/bin/bash
############################################################################################################
##                                 Database Deployment Pipeline                                           ##
##                                                                                                        ##
## This Script is developed by Shankar N G                                                                ##
## It is to trigger the Flask Application of the Database Deployment Pipeline                             ##
## The Flask App provides the web interface to manage and trigger the deployment pipeline                  ##
## Please edit the APP_DIR path to point to where the application is installed                            ##
## Make sure the virtual environment and requirements are set up before running                            ##
## This Script is for Linux Terminal                                                                      ##
############################################################################################################

APP_DIR=~/PythonProjects/databaseDeploymentPipelineTool/flaskapp/app
LOG_DIR=$APP_DIR/logs
LOG_FILE=$LOG_DIR/flaskapp_$(date +%Y%m%d_%H%M%S).log

mkdir -p "$LOG_DIR"

echo "=============================================="
echo "  Starting Database Deployment Pipeline"
echo "  Component  : Flask Web Application"
echo "  Started at : $(date)"
echo "  Logs       : $LOG_FILE"
echo "=============================================="

cd "$APP_DIR" || { echo "ERROR: Application directory not found: $APP_DIR"; exit 1; }

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated."
else
    echo "WARNING: Virtual environment not found. Running with system Python."
fi

nohup python -m main >> "$LOG_FILE" 2>&1 &

APP_PID=$!
echo "Flask App started with PID: $APP_PID"
echo "To stop the application, run: kill $APP_PID"
echo "To view logs, run: tail -f $LOG_FILE"

echo $APP_PID > "$APP_DIR/flaskapp.pid"
echo "PID saved to: $APP_DIR/flaskapp.pid"

deactivate 2>/dev/null

echo "=============================================="
echo "  Flask App is running in the background"
echo "=============================================="
