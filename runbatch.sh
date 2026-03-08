#!/bin/bash
############################################################################################################
##                                 Database Deployment Pipeline                                           ##
##                                                                                                        ##
## This Script is developed by Shankar N G                                                                ##
## It is to trigger the Batch Process of the Database Deployment Pipeline                                 ##
## The Batch Process moves the ETL files and executes the SQL scripts against the database                ##
## Please edit the APP_DIR path to point to where the application is installed                            ##
## Make sure the virtual environment and requirements are set up before running                            ##
## This Script is for Linux Terminal                                                                      ##
############################################################################################################

APP_DIR=~/PythonProjects/databaseDeploymentPipelineTool/batchprocess/app
LOG_DIR=$APP_DIR/logs
LOG_FILE=$LOG_DIR/batchprocess_$(date +%Y%m%d_%H%M%S).log

mkdir -p "$LOG_DIR"

echo "=============================================="
echo "  Starting Database Deployment Pipeline"
echo "  Component  : Batch Process"
echo "  Started at : $(date)"
echo "  Logs       : $LOG_FILE"
echo "=============================================="

cd "$APP_DIR/batchprocess/app" || { echo "ERROR: Batch process directory not found: $APP_DIR/batchprocess/app"; exit 1; }

if [ -f "$APP_DIR/.venv/bin/activate" ]; then
    source "$APP_DIR/.venv/bin/activate"
    echo "Virtual environment activated."
else
    echo "WARNING: Virtual environment not found. Running with system Python."
fi

nohup python -m main >> "$LOG_FILE" 2>&1 &

APP_PID=$!
echo "Batch Process started with PID: $APP_PID"
echo "To stop the process, run: kill $APP_PID"
echo "To view logs, run: tail -f $LOG_FILE"

echo $APP_PID > "$APP_DIR/batchprocess.pid"
echo "PID saved to: $APP_DIR/batchprocess.pid"

deactivate 2>/dev/null

echo "=============================================="
echo "  Batch Process is running in the background"
echo "=============================================="
