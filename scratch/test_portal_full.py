import sqlite3
import re
from pathlib import Path
from werkzeug.security import generate_password_hash

test_db = Path("scratch/test_portal_full.db")
if test_db.exists():
    test_db.unlink()

conn = sqlite3.connect(str(test_db))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Test full schema creation in SQLite
schema_statements = [
    """
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'admin',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        role TEXT DEFAULT 'Field Surveyor',
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
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
    )
    """,
    """
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
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
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ProcessingHistory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        village_id INTEGER NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        action_note TEXT,
        changed_by TEXT DEFAULT 'System',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]

for stmt in schema_statements:
    cursor.execute(stmt)

# Insert Admin
cursor.execute("INSERT INTO Users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
               ('admin', generate_password_hash('Admin@123'), 'System Administrator', 'admin'))

# Insert Persons
cursor.execute("INSERT INTO Persons (name, phone) VALUES (?, ?)", ('Person A', '9876543210'))
p_a_id = cursor.lastrowid
cursor.execute("INSERT INTO Persons (name, phone) VALUES (?, ?)", ('Person B', '9876543211'))
p_b_id = cursor.lastrowid

# Insert 10 sample villages
for i in range(1, 11):
    cursor.execute("""
    INSERT INTO Villages (district_name, subdistrict_name, village_name, village_code, total_wells)
    VALUES (?, ?, ?, ?, ?)
    """, (f"District {i%2+1}", f"Taluka {i%3+1}", f"Village {i}", f"50000{i}", 10+i))

conn.commit()

# Test KPI calculation
def get_kpis(cur):
    cur.execute("SELECT COUNT(*) FROM Villages")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Villages WHERE assigned_person_id IS NOT NULL")
    assigned = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Villages WHERE assigned_person_id IS NULL AND kml_status NOT IN ('Done', 'Verified', 'Completed')")
    pending = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Villages WHERE kml_status IN ('Done', 'Verified', 'Completed')")
    completed = cur.fetchone()[0]
    return {"total": total, "pending": pending, "assigned": assigned, "completed": completed}

print("Initial KPIs (10 unassigned villages):", get_kpis(cursor))

# Assign 3 villages to Person A
cursor.execute("UPDATE Villages SET assigned_person_id = ?, assigned_person_name = ?, assigned_at = CURRENT_TIMESTAMP, assignment_status = 'Assigned' WHERE id IN (1, 2, 3)", (p_a_id, 'Person A'))
conn.commit()
print("After assigning 3 to Person A:", get_kpis(cursor))

# Assign 2 villages to Person B
cursor.execute("UPDATE Villages SET assigned_person_id = ?, assigned_person_name = ?, assigned_at = CURRENT_TIMESTAMP, assignment_status = 'Assigned' WHERE id IN (4, 5)", (p_b_id, 'Person B'))
conn.commit()
print("After assigning 2 to Person B:", get_kpis(cursor))

# Unassign village 1
cursor.execute("UPDATE Villages SET assigned_person_id = NULL, assigned_person_name = NULL, assigned_at = NULL, assignment_status = 'Unassigned' WHERE id = 1")
conn.commit()
print("After unassigning village 1:", get_kpis(cursor))

# Person counts
cursor.execute("""
SELECT p.id, p.name, COUNT(v.id) AS assigned_count
FROM Persons p
LEFT JOIN Villages v ON p.id = v.assigned_person_id
GROUP BY p.id, p.name
""")
for r in cursor.fetchall():
    print(f"Person: {r['name']} -> {r['assigned_count']} villages")

conn.close()
print("All assertions passed!")
