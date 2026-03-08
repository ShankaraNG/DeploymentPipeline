# Database Deployment Pipeline

A Python-based deployment pipeline that automates ETL file movements and database script execution — developed by Shankara Narayana N G.

---

## 📖 Overview

The Database Deployment Pipeline streamlines the deployment process by cloning a Git repository and then performing two key operations:

- 📂 **File Movement** — Reads the file movement properties, locates the required files in the cloned repository, and moves them to their designated target paths on the server where they can be accessed for ETL runs
- 🗄️ **Database Script Execution** — Reads the SQL properties, connects to the target database using the SQL client, and executes the deployment scripts. Rollback scripts are also available if the deployment needs to be undone

The pipeline has two independently runnable components — a **Batch Process** and a **Flask Web Application**.

> ⚠️ Make sure to verify the **system configuration** and all values in the **configuration properties files** before starting the pipeline. Contact Shankar for more information.

---

## ⚙️ Prerequisites

- Python 3.x installed
- SQL client installed and configured on the server
- Git installed and accessible from the command line
- Access to the target Git repository
- Dependencies installed from `requirements.txt`

---

## 🚀 Running the Application

### Batch Process

```bash
cd batchprocess/app
python -m main
```

### Flask Web Application

```bash
cd flaskapp/app
python -m main
```

Both components can be run independently depending on your deployment needs.

---

## 📁 Git Repository Structure

The pipeline clones the deployment repository from Git to local before processing. The repository must follow this structure:

```
<root>/
├── configmaps/
│   └── <servername>/
│       ├── filesmove.properties
│       ├── sqlfiles.properties
│       └── sqlrollbackfiles.properties
│
└── files/
    ├── filesmove/
    │   └── <subfolder>/
    │       └── <filename>
    ├── sqlscripts/
    │   └── <subfolder>/
    │       └── <script.sql>
    └── sqlrollback/
        └── <subfolder>/
            └── <rollback.sql>
```

---

## 🗂️ How the Repository is Organised

### `configmaps/`

Contains a folder named after the **target server**. Inside it are the three properties files that instruct the pipeline on what to move, what to execute, and how to connect to the database.

### `files/`

Contains the actual files and scripts to be deployed. It is divided into three subfolders:

- **`filesmove/`** — Holds the files to be moved to the server. Files are organised into subfolders as defined in `filesmove.properties`
- **`sqlscripts/`** — Holds the SQL deployment scripts. Files are organised into subfolders as defined in `sqlfiles.properties`
- **`sqlrollback/`** — Holds the SQL rollback scripts. Files are organised into subfolders as defined in `sqlrollbackfiles.properties`

---

## 🔧 Configuration Properties Files

### `filesmove.properties`

Instructs the pipeline which file to pick up, from which subfolder inside `files/filesmove/`, and where to place it on the server.

```
filename|subfolder|targetfolder
shankar.txt|processing|E:\PythonCertificates\databaseDeploymentPipelineTool\flaskapp\workingdirectory\
```

| Column | Description |
|---|---|
| `filename` | Name of the file to be moved |
| `subfolder` | Subfolder inside `files/filesmove/` where the file lives |
| `targetfolder` | Destination path on the server where the file should be placed |

---

### `sqlfiles.properties`

Instructs the pipeline which SQL script to execute, from which subfolder inside `files/sqlscripts/`, and the database connection details to use.

```
filename|subfolder|dbHostname|dbPort|dbServicename|dbUser|dbPassword
```

| Column | Description |
|---|---|
| `filename` | Name of the SQL script to execute |
| `subfolder` | Subfolder inside `files/sqlscripts/` where the script lives |
| `dbHostname` | Hostname of the target database server |
| `dbPort` | Port number of the database |
| `dbServicename` | Database service name |
| `dbUser` | Database username |
| `dbPassword` | Database password |

---

### `sqlrollbackfiles.properties`

Same structure as `sqlfiles.properties` but points to scripts inside `files/sqlrollback/`. Used to undo the deployment if something goes wrong.

```
filename|subfolder|dbHostname|dbPort|dbServicename|dbUser|dbPassword
```

---

## 🔄 How the Pipeline Works

### File Movement

1. The pipeline clones the Git repository to local
2. It reads `filesmove.properties` from the `configmaps/<servername>/` folder
3. For each entry it navigates to `files/filesmove/<subfolder>/` in the cloned repo
4. It picks up the file matching the `filename` column
5. It moves the file to the `targetfolder` path on the server

### SQL Script Execution

1. The pipeline reads `sqlfiles.properties` from the `configmaps/<servername>/` folder
2. For each entry it navigates to `files/sqlscripts/<subfolder>/` in the cloned repo
3. It picks up the SQL script matching the `filename` column
4. It connects to the database using the connection details in the properties file
5. It executes the SQL script against the target database

### Rollback

If a deployment needs to be reversed, the pipeline reads `sqlrollbackfiles.properties` and follows the same process as above but picks scripts from `files/sqlrollback/` instead.

---

## 👤 Author

**Shankara N G**

For further details on setup, configuration, or usage — please contact Shankar directly.

---

## 📄 License

This project is for internal use. Please refer to your organization's usage policy.
