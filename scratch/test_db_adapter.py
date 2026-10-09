import sqlite3
import re
from pathlib import Path

db_path = Path("scratch/test_portal.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Test table creation
cursor.execute("""
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
""")

cursor.execute("INSERT INTO Persons (name, phone) VALUES (?, ?)", ("Ramesh Patel", "9876543210"))
pid = cursor.lastrowid
print("Inserted Person ID:", pid)

cursor.execute("SELECT * FROM Persons WHERE id = ?", (pid,))
row = cursor.fetchone()
print("Fetched Person:", row)
conn.close()
print("SQLite test succeeded!")
