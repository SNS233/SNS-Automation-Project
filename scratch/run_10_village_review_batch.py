import requests
import time
import json
from pathlib import Path

# 1. Login to local portal
s = requests.Session()
login_resp = s.post("http://127.0.0.1:5000/api/auth/login", json={
    "username": "admin",
    "password": "Admin@123"
})
print("Portal login:", login_resp.json())

# 2. Start automation job with 1 worker (sequential) and auto_review_correct=true
excel_file = Path("scratch/test_10_villages.xlsx")
t0 = time.time()

with open(excel_file, 'rb') as f:
    start_resp = s.post(
        "http://127.0.0.1:5000/api/automation/start",
        files={'file': ('test_10_villages.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
        data={
            'concurrency': '1',
            'engine_mode': 'direct',
            'auto_review_correct': 'true',
            'force_fresh': 'true'
        }
    )

start_data = start_resp.json()
print("Start response:", start_data)

if not start_data.get('success'):
    print("Start failed:", start_data)
    exit(1)

job_id = start_data['data']['job_id']
print(f"Tracking Job: {job_id}")

# 3. Poll progress until complete
last_count = -1
while True:
    time.sleep(2.0)
    status_resp = s.get("http://127.0.0.1:5000/api/automation/status")
    st = status_resp.json().get('data', {})
    
    proc = st.get('processed_count', 0)
    total = st.get('total_villages', 0)
    comp = st.get('completed_count', 0)
    failed = st.get('failed_count', 0)
    curr_v = st.get('current_village', '-')
    status_msg = st.get('current_status', '-')
    speed = st.get('avg_speed_seconds', '-')
    eta = st.get('estimated_remaining_time', '-')

    if proc != last_count:
        last_count = proc
        print(f"[{time.strftime('%H:%M:%S')}] Progress: {proc}/{total} | Success: {comp} | Failed: {failed} | Speed: {speed}s/v | ETA: {eta} | Active: {curr_v}")

    if st.get('status') in ('completed', 'stopped', 'failed'):
        print(f"\nJob finished with status: {st.get('status')}")
        break

total_duration = round(time.time() - t0, 2)
print(f"\nTotal execution time: {total_duration} seconds")
print(f"Results summary:")
for r in st.get('results', []):
    print(f"  - {r.get('village_name')} ({r.get('village_code')}): {r.get('status')} -> {r.get('generated_link')}")
    print(f"    Message: {r.get('message')}")
