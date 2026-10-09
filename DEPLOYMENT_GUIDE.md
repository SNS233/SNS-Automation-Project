# DEPLOYMENT GUIDE: MASTER BOREWELL & TUBEWELL MANAGEMENT PORTAL

This guide provides step-by-step instructions for deploying the **Master Borewell & Tubewell Management Portal** to Hostinger (cPanel / Cloud Python App / VPS) or any Windows/Linux production server running Microsoft SQL Server.

---

## 1. Architecture Overview

- **Application Type**: Python WSGI Web Application (Flask 3.x)
- **Frontend**: HTML5, Vanilla JavaScript, CSS3, Lucide Icons, Leaflet GIS, Chart.js
- **Database**: Microsoft SQL Server (2017 / 2019 / 2022 / Azure SQL)
- **ODBC Driver**: `ODBC Driver 18 for SQL Server` or `ODBC Driver 17 for SQL Server`
- **WSGI Entrypoints**: `passenger_wsgi.py` (Hostinger/cPanel) and `wsgi.py` (Gunicorn / uWSGI)

---

## 2. Hostinger Cloud / cPanel Python App Deployment

Hostinger provides Python application hosting powered by CloudLinux / LiteSpeed / Phusion Passenger.

### Step 1: Create the Python App in Hostinger hPanel / cPanel
1. Log in to your Hostinger control panel.
2. Navigate to **Advanced** &rarr; **Python Application** (or **Setup Python App**).
3. Click **Create Application**.
4. Configure the application:
   - **Python Version**: Select `Python 3.11`, `3.12`, or `3.13`.
   - **Application Root**: e.g., `borewell-portal` (or your domain folder).
   - **Application URL**: Select your domain or subdomain (e.g., `borewell.yourdomain.com`).
   - **Application Startup File**: `passenger_wsgi.py`
   - **Application Entry Point**: `application`
5. Click **Create**.

### Step 2: Upload Application Files
1. In Hostinger File Manager or via SFTP/Git, upload the project directory contents to your Application Root:
   ```
   borewell-portal/
   ├── app.py
   ├── config.py
   ├── db.py
   ├── wsgi.py
   ├── passenger_wsgi.py
   ├── requirements.txt
   ├── schema.sql
   ├── services/
   ├── routes/
   ├── static/
   ├── templates/
   └── uploads/
       ├── excel/
       ├── kml/
       └── errors/
   ```
2. Ensure write permissions (`755` or `775`) are granted to `uploads/`, `uploads/excel/`, `uploads/kml/`, and `uploads/errors/`.

### Step 3: Install Python Dependencies
1. Connect via SSH to your Hostinger server (or use the terminal in cPanel).
2. Activate the virtual environment provided by Hostinger:
   ```bash
   source /home/your_username/virtualenv/borewell-portal/3.11/bin/activate
   cd /home/your_username/borewell-portal
   ```
3. Install required packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Step 4: Configure Environment Variables
Create a file named `.env` in the root directory:
```bash
SECRET_KEY=generate-a-strong-random-64-char-string

# Remote Microsoft SQL Server Credentials
DB_SERVER=your-sql-server-ip-or-hostname
DB_PORT=1433
DB_NAME=BorewellPortalDB
DB_USER=your_sql_user
DB_PASSWORD=your_sql_password
DB_TRUSTED_CONNECTION=no
DB_ENCRYPT=yes
DB_TRUST_SERVER_CERTIFICATE=yes

# External Marking Portal URL
MARKING_PORTAL_URL=https://generate.snsies.com/

FLASK_DEBUG=False
PORT=5000
HOST=0.0.0.0
```

### Step 5: Initialize the SQL Server Database
Run the initial database setup script:
```bash
python -c "import db; db.init_db()"
```
This automatically ensures the database exists, creates all required tables (`Users`, `Villages`, `KMLFiles`, `ImportBatches`, `ProcessingHistory`, `ApplicationSettings`), and seeds the default administrator account:
- **Default Username**: `admin`
- **Default Password**: `Admin@123`

### Step 6: Restart the Application
In Hostinger Python App Manager, click **Restart Application**.
Visit your domain to verify the login screen appears!

---

## 3. Microsoft SQL Server Setup & Remote Connection

If your SQL Server is hosted on a dedicated Windows Server, Azure SQL, or AWS RDS:

### Enabling SQL Server Authentication & Remote Access:
1. Open **SQL Server Management Studio (SSMS)** on the SQL Server machine.
2. Right-click the server instance &rarr; **Properties** &rarr; **Security**.
3. Select **SQL Server and Windows Authentication mode** (Mixed Mode).
4. Under **SQL Server Configuration Manager**:
   - Ensure **TCP/IP** is enabled under **SQL Server Network Configuration**.
   - Under TCP/IP Properties &rarr; **IP Addresses**, verify `TCP Port` is set to `1433`.
5. Open Windows Firewall and create an Inbound Rule allowing TCP Port `1433`.
6. Create an application login:
   ```sql
   CREATE LOGIN [borewell_app_user] WITH PASSWORD = 'Strong_Password_2026!';
   USE [BorewellPortalDB];
   CREATE USER [borewell_app_user] FOR LOGIN [borewell_app_user];
   ALTER ROLE [db_owner] ADD MEMBER [borewell_app_user];
   ```

---

## 4. Local Development Execution (Windows)

To run the application locally on Windows:
```powershell
# 1. Clone/Navigate to workspace
cd "d:\Automation Project"

# 2. Verify requirements
pip install -r requirements.txt

# 3. Configure .env with your local settings
# (Windows Authentication is supported out of the box)
# DB_SERVER=localhost
# DB_NAME=BorewellPortalDB
# DB_TRUSTED_CONNECTION=yes

# 4. Run tests
python test_suite.py
python test_api.py

# 5. Start the web server
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
Log in using:
- **Username**: `admin`
- **Password**: `Admin@123`

---

## 5. Security & Maintenance Checklist

- [x] Change the default admin password in **Settings** &rarr; **Administrator Security** after first login.
- [x] Set `FLASK_DEBUG=False` in production.
- [x] Ensure `SECRET_KEY` is a unique 64-character hex string.
- [x] Secure `uploads/` directory with proper webserver MIME type restriction.
- [x] Parameterized SQL statements prevent SQL injection.
- [x] Transactional rollbacks protect data consistency during batch imports.
