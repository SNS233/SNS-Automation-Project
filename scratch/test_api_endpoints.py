import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from services.sync_service import get_state_version, bump_state_version

client = app.test_client()

print("=== TEST API 1: AUTHENTICATED HEARTBEAT AS ADMIN ===")
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'admin'

v = get_state_version()
resp = client.get(f'/api/system/heartbeat?version={v}')
assert resp.status_code == 200
data = resp.get_json()
print("Heartbeat with matching version:", data)
assert data['has_changed'] is False
assert data['unread_notifications'] >= 2

# Test with old version
resp_old = client.get(f'/api/system/heartbeat?version={v - 100}')
data_old = resp_old.get_json()
print("Heartbeat with older version:", data_old)
assert data_old['has_changed'] is True

print("\n=== TEST API 2: ADMIN DASHBOARD METRICS ===")
resp_dash = client.get('/api/dashboard/metrics')
assert resp_dash.status_code == 200
dash_data = resp_dash.get_json()
assert dash_data['success'] is True
summary = dash_data['data']['summary']
print(f"Metrics: Total={summary['total_villages']}, Completed={summary['completed_villages']}, Pending={summary['pending_villages']}")
assert summary['completed_villages'] == 8
assert summary['pending_villages'] == 20
assert summary['total_villages'] == 28

print("\n=== TEST API 3: SURVEYOR SESSION & SAVE ENDPOINT ===")
with client.session_transaction() as sess:
    sess['user_id'] = 5
    sess['username'] = 'ompatel'
    sess['full_name'] = 'Om Patel'
    sess['role'] = 'user'

# Test surveyor heartbeat
hb_surveyor = client.get(f'/api/system/heartbeat?version={v}').get_json()
print("Surveyor heartbeat:", hb_surveyor)
assert hb_surveyor['user_metrics']['assigned_villages'] == 5
assert hb_surveyor['user_metrics']['pending_villages'] == 3
assert hb_surveyor['user_metrics']['completed_villages'] == 2

# Save village 4 (ID 4) via HTTP POST
v_before = get_state_version()
post_resp = client.post('/api/user/villages/4/save', json={
    'dugwells': 4,
    'bores': 6,
    'total_wells': 10,
    'remark': 'Saved via HTTP POST route test',
    'mark_completed': True,
    'status': 'Done'
})
assert post_resp.status_code == 200
post_data = post_resp.get_json()
print("Save HTTP POST response:", post_data)
assert post_data['success'] is True
assert post_data['work_status'] == 'Done'

# Verify version was bumped
v_after = get_state_version()
assert v_after > v_before, "Version was not bumped after HTTP save"

# Verify metrics updated via HTTP
hb_after = client.get(f'/api/system/heartbeat?version={v_before}').get_json()
print("Heartbeat after HTTP save:", hb_after)
assert hb_after['has_changed'] is True
assert hb_after['user_metrics']['pending_villages'] == 2
assert hb_after['user_metrics']['completed_villages'] == 3

# Verify Admin dashboard metrics reflect this instantly
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['role'] = 'admin'

admin_dash = client.get('/api/dashboard/metrics').get_json()
print("Admin metrics after save:", admin_dash['data']['summary'])
assert admin_dash['data']['summary']['completed_villages'] == 9
assert admin_dash['data']['summary']['pending_villages'] == 19

print("\n=============================================")
print("ALL HTTP ROUTE TESTS PASSED 100%!")
print("=============================================")
