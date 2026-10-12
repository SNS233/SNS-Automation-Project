import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from app import create_app
from services.user_work_service import ensure_village_review_link

# Find or insert a real village for testing genuine link retrieval
v = db.query_one("SELECT id, village_name, village_code, generated_review_url FROM Villages WHERE village_code = '511639'")
if not v:
    # Insert test village record with genuine code
    vid = db.execute_scalar_insert(
        "INSERT INTO Villages (village_name, village_code, district_name, subdistrict_name, total_wells, kml_status, created_at) VALUES (?, ?, ?, ?, ?, ?, GETDATE())",
        ('Bharkunda', '511639', 'Ahmedabad', 'Daskroi', 42, 'Pending')
    )
    v = db.query_one("SELECT id, village_name, village_code, generated_review_url FROM Villages WHERE id = ?", (vid,))

print("Testing ensure_village_review_link on village:", v['village_name'], v['village_code'])
link = ensure_village_review_link(v['id'])
print("Resulting genuine review link:", link)
assert 'generate.snsies.com/villages/' in link and '/review' in link, f"Invalid link: {link}"
print("[PASS] Genuine review link acquired and verified!")
