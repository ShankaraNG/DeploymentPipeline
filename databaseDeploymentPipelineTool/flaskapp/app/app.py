from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import os
import sys
from werkzeug.utils import secure_filename
import services.mailing as mailing
import logger as logging
import configloader as cnfloader
import runconfigparser as runconfigparser
import services.pipelinedriver as pipelinedriver


app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production

try:
    config = cnfloader.load_properties()
    flaskHistoryPath = config.get('flaskHistoryDataPath')
    if not os.path.exists(flaskHistoryPath):
        raise ValueError((404,"File not found"))
    # DATA_FILE = os.path.join("data", flaskHistoryPath)
    DATA_FILE = flaskHistoryPath
except Exception as e:
        print(e)
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        if code in [400, 404]:
            sys.exit(1)    
# ===== ROUTES =====

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    user = request.form['username']
    password = request.form['password']
    # Basic authentication (replace with real logic)
    if user == "admin" and password == "admin":
        session['user'] = user
        return redirect(url_for('home'))
    else:
        flash("Invalid credentials!")
        return redirect(url_for('login'))

# @app.route('/home')
# def home():
#     if 'user' not in session:
#         return redirect(url_for('login'))
#     return render_template('home.html')

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    scheduled_text = None
    config = cnfloader.load_properties()
    try:
        bannerfile = config.get('batchschedulebannerfile')
        if not os.path.exists(bannerfile):
            raise ValueError((404,"File not found"))
    except Exception as e:
        if isinstance(e.args[0], tuple) and len(e.args[0]) == 2:
            code, message = e.args[0]
        else:
            code, message = 500, str(e)
        if code in [400, 404]:
            sys.exit(1)   
    file_path = bannerfile
    
    # Read the first non-empty line if file exists
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            line = f.readline().strip()
            if line:
                scheduled_text = line

    return render_template('home.html', scheduled_text=scheduled_text)

@app.route('/start_pipeline')
def start_pipeline():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('start_pipeline.html')

# @app.route('/run_pipeline', methods=['POST'])
# def run_pipeline():
#     # You can call your backend logic here
#     form_data = request.form.to_dict()
#     print("Pipeline started with data:", form_data)
#     flash("Pipeline started successfully!")
#     return redirect(url_for('home'))

@app.route('/run_pipeline', methods=['POST'])
def run_pipeline():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        # from yourpackage import logging, runconfigparser, pipelinedriver  # replace 'yourpackage' with the real module path

        # Get form data
        REPOURL = request.form.get('git_url')
        TARGETBRANCH = request.form.get('target_branch')
        Mode = request.form.get('mode')
        Type = request.form.get('type')
        servername = request.form.get('server_name')
        deploy = request.form.get('deploy')
        backfilename = request.form.get('backup_file')
        emaildistributionlist = request.form.get('email_list')

        # ===== Validation =====
        missing_fields = []
        for field_name, value in [
            ("Git URL", REPOURL),
            ("Target Branch", TARGETBRANCH),
            ("Mode", Mode),
            ("Type", Type),
            ("Server Name", servername),
            ("Deploy", deploy),
            ("Backup File", backfilename),
            ("Email List", emaildistributionlist)
        ]:
            if not value or value.strip() == "":
                missing_fields.append(field_name)

        if missing_fields:
            flash(f"Cannot start pipeline. Missing fields: {', '.join(missing_fields)}")
            return redirect(url_for('start_pipeline'))

        # Simple email validation
        if "@" not in emaildistributionlist or ".com" not in emaildistributionlist:
            flash("Invalid email address. It must contain '@' and '.com'")
            return redirect(url_for('start_pipeline'))
        
        if deploy.upper() not in ['TRUE', 'FALSE']:
            flash("Deploy field must be either 'True' or 'False'")
            return redirect(url_for('start_pipeline'))        

        if deploy.upper() == 'FALSE':
            flash("Pipeline has not started as the deployment is False")
            return redirect(url_for('start_pipeline'))
        
        # Generate pipeline number dynamically
        pipelineno = logging.loadnoupdate()

        # Create run configuration dynamically
        newconfigfile = runconfigparser.createRunConfiguration(pipelineno, Mode, Type, REPOURL, TARGETBRANCH, servername, deploy, backfilename, emaildistributionlist)

        if not newconfigfile:
            flash("Run configuration file not created")
            return redirect(url_for('start_pipeline'))

        pipelinedriver.pipelinedriver(pipelineno) # Comment this line if you want to test a smaple run with the actual code logic but without execution

        flash(f"Pipeline with no as {pipelineno} has been started successfully!")
        return redirect(url_for('pipeline_runs'))

    except Exception as e:
        print("Error running pipeline:")
        flash(f"Failed to start pipeline")
        return redirect(url_for('start_pipeline'))

@app.route('/pipeline_runs')
def pipeline_runs():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    runs = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            lines = f.readlines()[1:]  # skip header
            for line in lines:
                cols = line.strip().split('|')
                if len(cols) >= 10:
                    runs.append({
                        "PipelineNo": cols[0],
                        "StartTime": cols[1],
                        "LastUpdatedTime": cols[2],
                        "GitUrl": cols[3],
                        "Branch": cols[4],
                        "DeploymentType": cols[5],
                        "TriggeredBy": cols[6],
                        "Stage": cols[7],
                        "Status": cols[8],
                        "LogPath": cols[9]
                    })
        runs.sort(key=lambda x: int(x["PipelineNo"]), reverse=True)
    return render_template('pipeline_runs.html', runs=runs)

@app.route('/download_log/<path:logpath>')
def download_log(logpath):
    if 'user' not in session:
        return redirect(url_for('login'))
    if not os.path.exists(logpath):
        flash("Log file not found!")
        return redirect(url_for('pipeline_runs'))
    return send_file(logpath, as_attachment=True)

@app.route('/about')
def about():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('about.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
