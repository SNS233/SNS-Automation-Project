import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / '.env')

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv('SECRET_KEY', 'borewell-master-portal-secret-key-2026-secure')
    
    # SQL Server Settings
    DB_SERVER = os.getenv('DB_SERVER', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'BorewellPortalDB')
    DB_USER = os.getenv('DB_USER', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_PORT = os.getenv('DB_PORT', '1433')
    DB_DRIVER = os.getenv('DB_DRIVER', '')  # Auto-detected if blank
    DB_TRUSTED_CONNECTION = os.getenv('DB_TRUSTED_CONNECTION', 'yes' if not os.getenv('DB_USER') else 'no')
    DB_ENCRYPT = os.getenv('DB_ENCRYPT', 'no')
    DB_TRUST_SERVER_CERTIFICATE = os.getenv('DB_TRUST_SERVER_CERTIFICATE', 'yes')
    
    # Custom direct connection string (optional override)
    SQL_SERVER_CONN_STRING = os.getenv('SQL_SERVER_CONN_STRING', '')
    
    # Upload Directories
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    EXCEL_UPLOAD_DIR = UPLOAD_FOLDER / 'excel'
    KML_UPLOAD_DIR = UPLOAD_FOLDER / 'kml'
    ERROR_REPORT_DIR = UPLOAD_FOLDER / 'errors'
    AUTOMATION_UPLOAD_DIR = UPLOAD_FOLDER / 'automation'
    
    # Max Upload Size (e.g. 64 MB)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 64 * 1024 * 1024))
    
    # Portal Automation URL & Credentials (environment variables, never hardcoded)
    PORTAL_URL = os.getenv('PORTAL_URL') or os.getenv('MARKING_PORTAL_URL', 'https://generate.snsies.com/')
    MARKING_PORTAL_URL = PORTAL_URL
    PORTAL_USERNAME = os.getenv('PORTAL_USERNAME') or os.getenv('MARKING_PORTAL_USER', '')
    MARKING_PORTAL_USER = PORTAL_USERNAME
    PORTAL_PASSWORD = os.getenv('PORTAL_PASSWORD') or os.getenv('MARKING_PORTAL_PASSWORD', '')
    MARKING_PORTAL_PASSWORD = PORTAL_PASSWORD
    PORTAL_SESSION = os.getenv('PORTAL_SESSION') or os.getenv('MARKING_PORTAL_SESSION', '')
    MARKING_PORTAL_SESSION = PORTAL_SESSION
    PORTAL_HEADLESS = os.getenv('PORTAL_HEADLESS', 'true').lower() in ('true', '1', 'yes')
    
    # Server / App Settings
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')

    @classmethod
    def ensure_dirs(cls):
        cls.EXCEL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.KML_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.ERROR_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        cls.AUTOMATION_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
