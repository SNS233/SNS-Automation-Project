import os
import time
import datetime
import sqlite3
import re
import socket
import logging
from pathlib import Path
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from config import Config

logger = logging.getLogger(__name__)

# Track active database mode: 'sqlserver' or 'sqlite'
_db_mode = None
_cached_driver = None
_db_available_cache = {"status": None, "checked_at": 0}
SQLITE_DB_PATH = Config.BASE_DIR / 'borewell_portal.db'


def _can_connect_sqlserver():
    """Quickly check if SQL Server host and port are listening to avoid long connection timeouts."""
    server = (Config.DB_SERVER or '').split(',')[0].split('\\')[0].strip()
    if not server:
        return False
    port = int(Config.DB_PORT) if Config.DB_PORT and str(Config.DB_PORT).isdigit() else 1433
    try:
        with socket.create_connection((server, port), timeout=0.6):
            return True
    except Exception:
        return False


def get_best_driver():
    """Detect the best installed Microsoft SQL Server ODBC driver."""
    global _cached_driver
    if _cached_driver:
        return _cached_driver

    if Config.DB_DRIVER:
        _cached_driver = Config.DB_DRIVER
        return _cached_driver

    try:
        import pyodbc
        available_drivers = pyodbc.drivers()
    except Exception:
        return None

    preferred_order = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'ODBC Driver 13 for SQL Server',
        'ODBC Driver 11 for SQL Server',
        'SQL Server Native Client RDA 11.0',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]
    for d in preferred_order:
        if d in available_drivers:
            _cached_driver = d
            return d

    for d in available_drivers:
        if 'SQL Server' in d or 'SQLServer' in d:
            _cached_driver = d
            return d

    return None


def build_connection_string(database_name=None):
    """Build ODBC connection string for SQL Server."""
    if Config.SQL_SERVER_CONN_STRING:
        return Config.SQL_SERVER_CONN_STRING

    driver = get_best_driver()
    if not driver:
        return ""

    db = database_name if database_name is not None else Config.DB_NAME
    parts = [f"DRIVER={{{driver}}}", f"SERVER={Config.DB_SERVER}"]

    if Config.DB_PORT and Config.DB_PORT != '1433' and ',' not in Config.DB_SERVER:
        parts[1] = f"SERVER={Config.DB_SERVER},{Config.DB_PORT}"

    if db:
        parts.append(f"DATABASE={db}")

    trusted = Config.DB_TRUSTED_CONNECTION.lower() in ('yes', 'true', '1')
    if trusted:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={Config.DB_USER}")
        parts.append(f"PWD={Config.DB_PASSWORD}")

    if 'Driver 18' in driver:
        if Config.DB_TRUST_SERVER_CERTIFICATE.lower() in ('yes', 'true', '1'):
            parts.append("TrustServerCertificate=yes")
        if Config.DB_ENCRYPT.lower() in ('yes', 'true', '1'):
            parts.append("Encrypt=yes")
        else:
            parts.append("Encrypt=no")
    elif 'Driver 17' in driver:
        if Config.DB_TRUST_SERVER_CERTIFICATE.lower() in ('yes', 'true', '1'):
            parts.append("TrustServerCertificate=yes")

    return ";".join(parts) + ";"


def detect_db_mode(force_refresh=False):
    """Determine whether to use SQL Server or local SQLite."""
    global _db_mode
    if _db_mode and not force_refresh:
        return _db_mode

    # Check if SQL Server is configured and responding
    if _can_connect_sqlserver() and get_best_driver():
        try:
            import pyodbc
            conn_str = build_connection_string()
            conn = pyodbc.connect(conn_str, timeout=1)
            conn.close()
            _db_mode = 'sqlserver'
            logger.info("Connected to Microsoft SQL Server database.")
            return _db_mode
        except Exception as e:
            logger.warning(f"SQL Server ping failed ({e}). Using local database.")

    _db_mode = 'sqlite'
    logger.info(f"Using local database: {SQLITE_DB_PATH} (XAMPP-free, zero setup required).")
    return _db_mode


def adapt_sql(sql, params=None):
    """Translate SQL Server syntax into SQLite syntax when running in SQLite mode."""
    mode = detect_db_mode()
    params = list(params) if params else []
    if mode == 'sqlserver':
        return sql, params

    # SQLite adaptations:
    # 1. ISNULL -> COALESCE
    sql = re.sub(r'\bISNULL\s*\(', 'COALESCE(', sql, flags=re.IGNORECASE)

    # 2. GETDATE() -> CURRENT_TIMESTAMP
    sql = re.sub(r'\bGETDATE\s*\(\s*\)', 'CURRENT_TIMESTAMP', sql, flags=re.IGNORECASE)

    # 3. TOP N -> LIMIT N
    top_m = re.search(r'\bSELECT\s+TOP\s+(\d+)\s+', sql, flags=re.IGNORECASE)
    if top_m:
        top_n = top_m.group(1)
        sql = re.sub(r'\bSELECT\s+TOP\s+\d+\s+', 'SELECT ', sql, count=1, flags=re.IGNORECASE)
        sql = f"{sql.rstrip(';')} LIMIT {top_n}"

    # 4. OFFSET ? ROWS FETCH NEXT ? ROWS ONLY -> LIMIT ? OFFSET ?
    m = re.search(r'OFFSET\s+(\?|\d+)\s+ROWS\s+FETCH\s+NEXT\s+(\?|\d+)\s+ROWS\s+ONLY', sql, flags=re.IGNORECASE)
    if m:
        p1, p2 = m.group(1), m.group(2)
        if p1 == '?' and p2 == '?':
            if len(params) >= 2:
                # In SQL Server caller: [..., offset, page_size]
                # In SQLite: LIMIT page_size OFFSET offset
                params[-2], params[-1] = params[-1], params[-2]
            sql = sql[:m.start()] + 'LIMIT ? OFFSET ?' + sql[m.end():]
        elif p1.isdigit() and p2.isdigit():
            sql = sql[:m.start()] + f'LIMIT {p2} OFFSET {p1}' + sql[m.end():]

    # 5. Remove OUTPUT INSERTED.id
    sql = re.sub(r'\s+OUTPUT\s+INSERTED\.\w+\s+', ' ', sql, flags=re.IGNORECASE)

    return sql, params


def is_db_available(max_age_seconds=10):
    """Check if database connection is responsive."""
    return True


class AdaptedCursor:
    """Cursor wrapper that automatically translates SQL Server syntax to SQLite when offline."""
    def __init__(self, raw_cursor, mode):
        self._raw = raw_cursor
        self._mode = mode

    def execute(self, sql, params=None):
        if self._mode == 'sqlite':
            sql, params = adapt_sql(sql, params)
        return self._raw.execute(sql, params or [])

    def executemany(self, sql, seq_of_params):
        if self._mode == 'sqlite':
            sql, _ = adapt_sql(sql, [])
        return self._raw.executemany(sql, seq_of_params)

    def __getattr__(self, name):
        return getattr(self._raw, name)


def get_db_connection(autocommit=False):
    """Open and return a database connection."""
    mode = detect_db_mode()
    if mode == 'sqlserver':
        import pyodbc
        conn_str = build_connection_string()
        return pyodbc.connect(conn_str, timeout=2, autocommit=autocommit)
    else:
        conn = sqlite3.connect(str(SQLITE_DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row
        # Register compatibility functions for raw SQL execution
        conn.create_function('GETDATE', 0, lambda: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        conn.create_function('ISNULL', 2, lambda val, default: default if val is None else val)
        if autocommit:
            conn.isolation_level = None
        return conn


@contextmanager
def get_db_cursor(commit=False):
    """Context manager for acquiring an adapted cursor, committing if requested, and closing properly."""
    mode = detect_db_mode()
    conn = get_db_connection(autocommit=False)
    cursor = conn.cursor()
    try:
        yield AdaptedCursor(cursor, mode)
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def row_to_dict(cursor, row):
    """Convert DB row to a standard Python dict."""
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def query_all(sql, params=None):
    """Execute a SELECT query and return all rows as list of dicts."""
    mode = detect_db_mode()
    sql, params = adapt_sql(sql, params)
    with get_db_cursor() as cursor:
        cursor.execute(sql, params or [])
        if mode == 'sqlite':
            return [dict(row) for row in cursor.fetchall()]
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def query_one(sql, params=None):
    """Execute a SELECT query and return a single dict or None."""
    mode = detect_db_mode()
    sql, params = adapt_sql(sql, params)
    with get_db_cursor() as cursor:
        cursor.execute(sql, params or [])
        row = cursor.fetchone()
        if not row:
            return None
        if mode == 'sqlite':
            return dict(row)
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))


def execute_non_query(sql, params=None):
    """Execute an INSERT, UPDATE, or DELETE statement and return rowcount."""
    sql, params = adapt_sql(sql, params)
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(sql, params or [])
        return cursor.rowcount


def execute_scalar_insert(sql, params=None):
    """Execute an INSERT and return the newly generated ID."""
    mode = detect_db_mode()
    sql, params = adapt_sql(sql, params)
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(sql, params or [])
        if mode == 'sqlite':
            return cursor.lastrowid
        else:
            try:
                row = cursor.fetchone()
                if row:
                    return row[0]
            except Exception:
                pass
            cursor.execute("SELECT SCOPE_IDENTITY()")
            row = cursor.fetchone()
            return row[0] if row else None


def check_db_health():
    """Verify database connection and return health summary."""
    mode = detect_db_mode()
    try:
        if mode == 'sqlserver':
            row = query_one("SELECT @@VERSION AS ver, DB_NAME() AS db, GETDATE() AS server_time")
            return {
                "status": "healthy",
                "connected": True,
                "engine": "Microsoft SQL Server",
                "database": row["db"],
                "server_time": str(row["server_time"]),
                "version_summary": str(row["ver"]).split('\n')[0]
            }
        else:
            row = query_one("SELECT sqlite_version() AS ver, CURRENT_TIMESTAMP AS server_time")
            return {
                "status": "healthy",
                "connected": True,
                "engine": "Local SQLite Database",
                "database": str(SQLITE_DB_PATH.name),
                "server_time": str(row["server_time"]),
                "version_summary": f"SQLite v{row['ver']} (Standalone, XAMPP-Free)"
            }
    except Exception as e:
        return {"status": "unhealthy", "connected": False, "error": str(e)}


def init_db():
    """Initialize database tables, schema columns, and default administrator account."""
    mode = detect_db_mode()
    logger.info(f"Initializing database using engine: {mode.upper()}...")

    if mode == 'sqlserver':
        _init_sqlserver()
    else:
        _init_sqlite()

    # Ensure default admin user exists
    user = query_one("SELECT id FROM Users WHERE username = ?", ('admin',))
    if not user:
        default_hash = generate_password_hash('Admin@123')
        execute_non_query(
            "INSERT INTO Users (username, password_hash, full_name, role, is_active) VALUES (?, ?, ?, ?, ?)",
            ('admin', default_hash, 'System Administrator', 'admin', 1)
        )
        logger.info("Default administrator account 'admin' created with password 'Admin@123'.")

    return True


def _init_sqlite():
    """Create or upgrade SQLite database tables."""
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'admin',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS Persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        role TEXT DEFAULT 'Field Surveyor',
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ImportBatches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT,
        total_rows INTEGER DEFAULT 0,
        valid_rows INTEGER DEFAULT 0,
        invalid_rows INTEGER DEFAULT 0,
        duplicate_rows INTEGER DEFAULT 0,
        status TEXT DEFAULT 'completed',
        error_report_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS Villages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        zone TEXT,
        district_name TEXT NOT NULL,
        subdistrict_name TEXT NOT NULL,
        village_name TEXT NOT NULL,
        village_code TEXT NOT NULL,
        geb_connection TEXT,
        google_search_orig_nos INTEGER DEFAULT 0,
        google_edited_nos INTEGER DEFAULT 0,
        total_wells INTEGER DEFAULT 0,
        dugwells INTEGER DEFAULT 0,
        bores INTEGER DEFAULT 0,
        kml_status TEXT DEFAULT 'Pending',
        remark TEXT,
        processing_order INTEGER DEFAULT 0,
        is_locked INTEGER DEFAULT 0,
        last_processed_at TIMESTAMP,
        assigned_person_id INTEGER,
        assigned_person_name TEXT,
        assigned_at TIMESTAMP,
        assignment_status TEXT DEFAULT 'Unassigned',
        electric_kuva INTEGER DEFAULT 0,
        electric_bor INTEGER DEFAULT 0,
        total_electric INTEGER DEFAULT 0,
        solar_bor_kuva INTEGER DEFAULT 0,
        total_electric_solar INTEGER DEFAULT 0,
        raw_geb_data TEXT,
        generated_review_url TEXT,
        work_status TEXT DEFAULT 'Not Done',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS VillageAssignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        village_id INTEGER NOT NULL,
        person_id INTEGER NOT NULL,
        assigned_by TEXT DEFAULT 'Admin',
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        unassigned_at TIMESTAMP,
        status TEXT DEFAULT 'Active'
    );

    CREATE TABLE IF NOT EXISTS AdminNotifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT NOT NULL,
        village_id INTEGER NOT NULL,
        village_name TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS KMLFiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        village_id INTEGER NOT NULL,
        village_code TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        stored_filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        point_count INTEGER DEFAULT 0,
        polygon_count INTEGER DEFAULT 0,
        linestring_count INTEGER DEFAULT 0,
        total_placemarks INTEGER DEFAULT 0,
        geojson_data TEXT,
        bounds_json TEXT,
        version INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        validation_status TEXT DEFAULT 'Valid',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ProcessingHistory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        village_id INTEGER NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        action_note TEXT,
        changed_by TEXT DEFAULT 'System',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS IX_Villages_VillageCode ON Villages(village_code);
    CREATE INDEX IF NOT EXISTS IX_Villages_Status ON Villages(kml_status);
    CREATE INDEX IF NOT EXISTS IX_Villages_District ON Villages(district_name);
    CREATE INDEX IF NOT EXISTS IX_Villages_Subdistrict ON Villages(subdistrict_name);
    CREATE INDEX IF NOT EXISTS IX_Villages_AssignedPerson ON Villages(assigned_person_id);
    CREATE INDEX IF NOT EXISTS IX_Villages_WorkStatus ON Villages(work_status);
    CREATE INDEX IF NOT EXISTS IX_AdminNotifications_IsRead ON AdminNotifications(is_read);
    """)

    # Ensure any missing columns in existing Villages table are added dynamically
    cursor.execute("PRAGMA table_info(Villages)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    migrations = [
        ("assigned_person_id", "INTEGER"),
        ("assigned_person_name", "TEXT"),
        ("assigned_at", "TIMESTAMP"),
        ("assignment_status", "TEXT DEFAULT 'Unassigned'"),
        ("electric_kuva", "INTEGER DEFAULT 0"),
        ("electric_bor", "INTEGER DEFAULT 0"),
        ("total_electric", "INTEGER DEFAULT 0"),
        ("solar_bor_kuva", "INTEGER DEFAULT 0"),
        ("total_electric_solar", "INTEGER DEFAULT 0"),
        ("raw_geb_data", "TEXT"),
        ("generated_review_url", "TEXT"),
        ("work_status", "TEXT DEFAULT 'Not Done'")
    ]
    for col_name, col_type in migrations:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE Villages ADD COLUMN {col_name} {col_type}")

    # Ensure user_id in Persons table
    cursor.execute("PRAGMA table_info(Persons)")
    existing_person_cols = {row[1] for row in cursor.fetchall()}
    if "user_id" not in existing_person_cols:
        cursor.execute("ALTER TABLE Persons ADD COLUMN user_id INTEGER")

    conn.commit()
    conn.close()
    logger.info("SQLite database schema initialized successfully.")


def _init_sqlserver():
    """Create or upgrade SQL Server database schema."""
    import pyodbc
    master_conn_str = build_connection_string(database_name='master')
    try:
        conn = pyodbc.connect(master_conn_str, timeout=3, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{Config.DB_NAME}') CREATE DATABASE [{Config.DB_NAME}]")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not connect to master database: {e}")

    # Schema script execution
    schema_file = Config.BASE_DIR / 'schema.sql'
    if schema_file.exists():
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        batches = [b.strip() for b in sql_script.split('GO') if b.strip()]
        conn = pyodbc.connect(build_connection_string(), timeout=3, autocommit=True)
        cursor = conn.cursor()
        for batch in batches:
            cleaned = batch.strip()
            if cleaned.upper().startswith('CREATE DATABASE') or cleaned.upper().startswith('USE '):
                continue
            if not cleaned:
                continue
            try:
                cursor.execute(cleaned)
            except Exception as e:
                logger.debug(f"SQL Server schema execution notice: {e}")
        cursor.close()
        conn.close()
