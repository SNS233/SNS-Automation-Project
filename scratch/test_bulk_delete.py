import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import db
from app import app
from services.village_service import bulk_delete_unassigned_villages, get_dashboard_metrics
from services.sync_service import get_state_version

client = app.test_client()

print("==================================================================")
print("TEST SUITE: BULK DELETE FOR SELECTED UNASSIGNED VILLAGES")
print("==================================================================")

# 1. Setup fresh sample test villages in DB for isolated testing
print("\n--- TEST CASE 1: PREPARING TEST DATA ---")
# Create 5 temporary unassigned villages
test_village_ids = []
for i in range(1, 6):
    code = f"TEST_BULK_{i}_{int(os.getpid())}"
    vid = db.execute_scalar_insert(
        """
        INSERT INTO Villages (village_name, village_code, district_name, subdistrict_name, zone,
                              assigned_person_id, assignment_status, work_status, kml_status,
                              total_wells, dugwells, bores, created_at, updated_at)
        VALUES (?, ?, 'BulkDistrict', 'BulkTaluka', 'ZoneA', NULL, 'Unassigned', 'Not Done', 'Pending', 5, 2, 3, GETDATE(), GETDATE())
        """,
        (f"Bulk Test Village {i}", code)
    )
    test_village_ids.append(vid)

print(f"Created 5 test unassigned villages: {test_village_ids}")
assert len(test_village_ids) == 5

# Also create 1 assigned village and 1 completed village for safety tests
assigned_vid = db.execute_scalar_insert(
    """
    INSERT INTO Villages (village_name, village_code, district_name, subdistrict_name, zone,
                          assigned_person_id, assigned_person_name, assignment_status, work_status, kml_status,
                          total_wells, dugwells, bores, created_at, updated_at)
    VALUES ('Assigned Test Village', 'TEST_ASSIGNED_SAFE', 'BulkDistrict', 'BulkTaluka', 'ZoneA', 8, 'Om Patel', 'Assigned', 'Not Done', 'Pending', 5, 2, 3, GETDATE(), GETDATE())
    """
)

completed_vid = db.execute_scalar_insert(
    """
    INSERT INTO Villages (village_name, village_code, district_name, subdistrict_name, zone,
                          assigned_person_id, assignment_status, work_status, kml_status,
                          total_wells, dugwells, bores, created_at, updated_at)
    VALUES ('Completed Test Village', 'TEST_DONE_SAFE', 'BulkDistrict', 'BulkTaluka', 'ZoneA', NULL, 'Unassigned', 'Done', 'Done', 5, 2, 3, GETDATE(), GETDATE())
    """
)

print(f"Created assigned safety village: {assigned_vid}")
print(f"Created completed safety village: {completed_vid}")

# 2. Test Empty / Invalid Requests
print("\n--- TEST CASE 2: EMPTY OR INVALID REQUEST VALIDATION ---")
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'admin'

res_empty = client.post('/api/villages/bulk-delete', json={'village_ids': []})
assert res_empty.status_code == 400
print("Empty village_ids rejected properly with 400:", res_empty.get_json())

res_invalid = client.post('/api/villages/bulk-delete', json={'village_ids': 'not-a-list'})
assert res_invalid.status_code == 400
print("Invalid village_ids type rejected with 400:", res_invalid.get_json())

# 3. Test Authorization: Non-admin user cannot delete
print("\n--- TEST CASE 3: NON-ADMIN AUTHORIZATION GUARD ---")
with client.session_transaction() as sess:
    sess['user_id'] = 5
    sess['username'] = 'ompatel'
    sess['role'] = 'user'

res_unauth = client.post('/api/villages/bulk-delete', json={'village_ids': [test_village_ids[0]]})
assert res_unauth.status_code == 403
print("Non-admin user blocked properly with 403:", res_unauth.get_json())

# 4. Test Single Village Bulk Delete (select 1 village)
print("\n--- TEST CASE 4: SINGLE VILLAGE BULK DELETE (SELECT 1 VILLAGE) ---")
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'admin'

v0 = get_state_version()
del_one_id = test_village_ids[0]
res_one = client.post('/api/villages/bulk-delete', json={'village_ids': [del_one_id], 'unassigned_only': True})
assert res_one.status_code == 200
data_one = res_one.get_json()
print("Single delete response:", data_one)
assert data_one['success'] is True
assert data_one['deleted_count'] == 1
assert data_one['failed_count'] == 0
assert data_one['deleted_villages'][0]['id'] == del_one_id

# Verify DB absence
row_check = db.query_one("SELECT id FROM Villages WHERE id = ?", (del_one_id,))
assert row_check is None, f"Village {del_one_id} was not deleted from DB!"
v1 = get_state_version()
assert v1 > v0, "State version was not bumped after deletion!"
print(f"Verified village {del_one_id} permanently deleted and state version bumped.")

# 5. Test Multiple Villages Bulk Delete (select 2 villages)
print("\n--- TEST CASE 5: MULTIPLE VILLAGES BULK DELETE (SELECT 2 VILLAGES) ---")
del_multi_ids = [test_village_ids[1], test_village_ids[2]]
res_multi = client.post('/api/villages/bulk-delete', json={'village_ids': del_multi_ids, 'unassigned_only': True})
assert res_multi.status_code == 200
data_multi = res_multi.get_json()
print("Multiple delete response:", data_multi)
assert data_multi['success'] is True
assert data_multi['deleted_count'] == 2
assert data_multi['failed_count'] == 0

for vid in del_multi_ids:
    row = db.query_one("SELECT id FROM Villages WHERE id = ?", (vid,))
    assert row is None, f"Village {vid} was not deleted from DB!"
print(f"Verified villages {del_multi_ids} permanently deleted from database.")

# 6. Test Data Safety: Assigned Villages Protection
print("\n--- TEST CASE 6: DATA SAFETY - ASSIGNED VILLAGE BLOCKED ---")
res_safe_assigned = client.post('/api/villages/bulk-delete', json={'village_ids': [assigned_vid], 'unassigned_only': True})
assert res_safe_assigned.status_code == 400
data_safe_assigned = res_safe_assigned.get_json()
print("Assigned village blocked response:", data_safe_assigned)
assert data_safe_assigned['deleted_count'] == 0
assert data_safe_assigned['failed_count'] == 1
assert "currently assigned" in data_safe_assigned['failed_villages'][0]['reason']

# Verify assigned village is STILL intact in DB
assigned_row = db.query_one("SELECT id, village_name FROM Villages WHERE id = ?", (assigned_vid,))
assert assigned_row is not None, "SAFETY VIOLATION: Assigned village was accidentally deleted!"
print("Assigned village remains safely intact in DB.")

# 7. Test Data Safety: Completed Survey Village Protection
print("\n--- TEST CASE 7: DATA SAFETY - COMPLETED SURVEY DATA BLOCKED ---")
res_safe_completed = client.post('/api/villages/bulk-delete', json={'village_ids': [completed_vid], 'unassigned_only': True})
assert res_safe_completed.status_code == 400
data_safe_completed = res_safe_completed.get_json()
print("Completed survey village blocked response:", data_safe_completed)
assert data_safe_completed['deleted_count'] == 0
assert data_safe_completed['failed_count'] == 1
assert "completed survey data" in data_safe_completed['failed_villages'][0]['reason']

completed_row = db.query_one("SELECT id, village_name FROM Villages WHERE id = ?", (completed_vid,))
assert completed_row is not None, "SAFETY VIOLATION: Completed survey village was accidentally deleted!"
print("Completed survey village remains safely intact in DB.")

# 8. Test Partial Failures: Mixed Batch (1 valid unassigned + 1 assigned + 1 completed + 1 non-existent)
print("\n--- TEST CASE 8: PARTIAL FAILURES - MIXED BATCH ---")
mixed_ids = [test_village_ids[3], assigned_vid, completed_vid, 9999999]
res_mixed = client.post('/api/villages/bulk-delete', json={'village_ids': mixed_ids, 'unassigned_only': True})
assert res_mixed.status_code == 200  # Partial success
data_mixed = res_mixed.get_json()
print("Mixed batch response:", data_mixed)
assert data_mixed['deleted_count'] == 1
assert data_mixed['failed_count'] == 3
assert data_mixed['deleted_villages'][0]['id'] == test_village_ids[3]

# Verify valid unassigned was deleted, but protected ones were NOT
assert db.query_one("SELECT id FROM Villages WHERE id = ?", (test_village_ids[3],)) is None
assert db.query_one("SELECT id FROM Villages WHERE id = ?", (assigned_vid,)) is not None
assert db.query_one("SELECT id FROM Villages WHERE id = ?", (completed_vid,)) is not None
print("Mixed batch handled safely: valid village deleted, protected villages preserved.")

# 9. Clean up remaining test records
print("\n--- TEST CASE 9: CLEANUP REMAINING TEST VILLAGES ---")
res_clean = bulk_delete_unassigned_villages([test_village_ids[4]], changed_by='Test', unassigned_only=False)
print("Cleaned up remaining unassigned village:", res_clean['deleted_count'])
db.execute_non_query("DELETE FROM Villages WHERE id IN (?, ?)", (assigned_vid, completed_vid))

print("\n==================================================================")
print("ALL 9 BULK DELETE TEST CASES PASSED WITH 100% SUCCESS!")
print("==================================================================")
