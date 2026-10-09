import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import db
from services.village_service import get_dashboard_metrics
from services.user_work_service import save_surveyor_village, get_user_assigned_villages, get_user_metrics
from services.sync_service import get_state_version, bump_state_version

print("=== STEP 1: SETUP 5 TEST VILLAGES FOR OM PATEL (USER ID 5, PERSON ID 8) ===")
test_ids = [2, 3, 4, 6, 9]

# Clean up and assign
for vid in test_ids:
    db.execute_non_query(
        "UPDATE Villages SET assigned_person_id = 8, work_status = 'Not Done', kml_status = 'Pending', dugwells = 0, bores = 0, total_wells = 0 WHERE id = ?",
        (vid,)
    )

# Unassign other villages from Om for clean test counting
db.execute_non_query(
    "UPDATE Villages SET assigned_person_id = NULL WHERE assigned_person_id = 8 AND id NOT IN (2, 3, 4, 6, 9)"
)

bump_state_version()
v0 = get_state_version()
print(f"Initial state version: {v0}")

# Check user metrics
m0 = get_user_metrics(5)
print("User metrics before saving:", m0)
assert m0['assigned_villages'] == 5, f"Expected 5 assigned, got {m0['assigned_villages']}"
assert m0['pending_villages'] == 5, f"Expected 5 pending, got {m0['pending_villages']}"
assert m0['completed_villages'] == 0, f"Expected 0 completed, got {m0['completed_villages']}"

active0 = get_user_assigned_villages(5)['items']
print(f"Active assigned villages count: {len(active0)}")
assert len(active0) == 5, f"Expected 5 active villages, got {len(active0)}"

print("\n=== STEP 2: SAVE ONLY VILLAGE 1 (ID 2) ===")
res1 = save_surveyor_village(
    village_id=2,
    user_id=5,
    user_name='Om Patel',
    data={'dugwells': 3, 'bores': 5, 'total_wells': 8, 'remark': 'Field survey complete', 'mark_completed': True, 'status': 'Done'}
)
print("Save response 1:", res1)
assert res1['success'] is True
assert res1['work_status'] == 'Done'

# Verify DB state of all 5 villages
rows = db.query_all("SELECT id, village_name, work_status, kml_status, dugwells, bores, total_wells FROM Villages WHERE id IN (2, 3, 4, 6, 9) ORDER BY id")
for r in rows:
    print("Village state:", r)

# CRITICAL ASSERTIONS: Only Village 2 must be Done!
assert rows[0]['work_status'] == 'Done', "Village 2 must be Done"
assert rows[0]['dugwells'] == 3 and rows[0]['bores'] == 5, "Village 2 wells mismatch"
for r in rows[1:]:
    assert r['work_status'] == 'Not Done', f"Village {r['id']} must remain Not Done!"
    assert r['kml_status'] == 'Pending', f"Village {r['id']} must remain Pending!"

m1 = get_user_metrics(5)
print("User metrics after saving Village 2:", m1)
assert m1['assigned_villages'] == 5, f"Assigned should be 5, got {m1['assigned_villages']}"
assert m1['pending_villages'] == 4, f"Pending should be 4, got {m1['pending_villages']}"
assert m1['completed_villages'] == 1, f"Completed should be 1, got {m1['completed_villages']}"

active1 = get_user_assigned_villages(5)['items']
print(f"Active assigned villages after saving 1: {len(active1)}")
assert len(active1) == 4, f"Expected 4 active villages, got {len(active1)}"
assert not any(v['id'] == 2 for v in active1), "Completed village 2 must be removed from active work list"

v1 = get_state_version()
print(f"Version after save 1: {v1}")
assert v1 > v0, "State version must have bumped"

print("\n=== STEP 3: SAVE VILLAGE 2 (ID 3) ===")
res2 = save_surveyor_village(
    village_id=3,
    user_id=5,
    user_name='Om Patel',
    data={'dugwells': 2, 'bores': 1, 'total_wells': 3, 'remark': 'Checked 2nd village', 'mark_completed': True, 'status': 'Done'}
)
print("Save response 2:", res2)
assert res2['success'] is True

rows2 = db.query_all("SELECT id, village_name, work_status, kml_status FROM Villages WHERE id IN (2, 3, 4, 6, 9) ORDER BY id")
for r in rows2:
    print("Village state:", r)

assert rows2[0]['work_status'] == 'Done'
assert rows2[1]['work_status'] == 'Done'
assert rows2[2]['work_status'] == 'Not Done', "Village 4 must still be Not Done"
assert rows2[3]['work_status'] == 'Not Done', "Village 6 must still be Not Done"
assert rows2[4]['work_status'] == 'Not Done', "Village 9 must still be Not Done"

m2 = get_user_metrics(5)
print("User metrics after saving Village 3:", m2)
assert m2['pending_villages'] == 3, f"Pending should be 3, got {m2['pending_villages']}"
assert m2['completed_villages'] == 2, f"Completed should be 2, got {m2['completed_villages']}"

active2 = get_user_assigned_villages(5)['items']
print(f"Active assigned villages after saving 2: {len(active2)}")
assert len(active2) == 3, f"Expected 3 active villages, got {len(active2)}"

print("\n=== STEP 4: VERIFY ADMIN DASHBOARD METRICS & PIE CHART DATA ===")
dash = get_dashboard_metrics()
summary = dash['summary']
print("Dashboard summary:", summary)
tot = summary['total_villages']
done = summary['completed_villages']
pend = summary['pending_villages']
print(f"Total: {tot}, Done: {done}, Pending: {pend}")
assert done + pend == tot, f"Done ({done}) + Pending ({pend}) != Total ({tot})"

print("\n=== STEP 5: VERIFY ADMIN NOTIFICATIONS CREATED ===")
notifs = db.query_all("SELECT user_name, village_name, message, is_read FROM AdminNotifications ORDER BY id DESC LIMIT 5")
for n in notifs:
    print("Notification:", n)
assert any("Test Village 2" in n['message'] or "Test Village 2" in n['village_name'] for n in notifs)
assert any("Test Village 3" in n['message'] or "Test Village 3" in n['village_name'] for n in notifs)

print("\n=============================================")
print("ALL VERIFICATIONS COMPLETED & PASSED 100%!")
print("=============================================")
