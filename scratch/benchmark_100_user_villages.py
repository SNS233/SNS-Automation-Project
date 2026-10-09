import openpyxl
import requests
import time
from pathlib import Path

# 1. Create a 100-village slice of the user's actual 2,971 village Excel file
src_path = "C:/Users/Admin/.gemini/antigravity/brain/00fe1a6c-ff00-4d9d-a57e-84b67982ddd1/.user_uploaded/media_1791280815428.xlsx"
src_wb = openpyxl.load_workbook(src_path, data_only=True)
src_ws = src_wb.active

dst_path = Path("scratch/user_sample_100.xlsx")
dst_wb = openpyxl.Workbook()
dst_ws = dst_wb.active
dst_ws.title = src_ws.title

# Copy header + first 100 data rows
for r in range(1, 102):
    row_vals = [src_ws.cell(r, c).value for c in range(1, src_ws.max_column + 1)]
    dst_ws.append(row_vals)

dst_wb.save(str(dst_path))
print(f"Created {dst_path} with 100 user village records.")

# 2. Login to local Flask portal
s = requests.Session()
s.post("http://127.0.0.1:5000/api/auth/login", json={"username": "admin", "password": "Admin@123"})

# 3. Start automation with 8 workers
t_start = time.time()
with open(dst_path, 'rb') as f:
    r = s.post("http://127.0.0.1:5000/api/automation/start", files={
        'file': ('user_sample_100.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }, data={'concurrency': '8', 'engine_mode': 'direct'})

job_data = r.json()
print("Start response:", job_data)
job_id = job_data['data']['job_id']

# 4. Monitor progress until completion
last_count = -1
while True:
    time.sleep(1.0)
    st = s.get("http://127.0.0.1:5000/api/automation/status").json()['data']
    if st['processed_count'] != last_count:
        last_count = st['processed_count']
        print(f"  Processed: {st['processed_count']}/100 | Success: {st['completed_count']} | Failed: {st['failed_count']} | Speed: {st['avg_speed_seconds']}s/vil | Throughput: {st['throughput_str']} | ETA: {st.get('estimated_remaining_time', '-')}")
    
    if st['status'] in ('completed', 'stopped', 'failed'):
        break

total_time = round(time.time() - t_start, 2)
avg_time = round(total_time / 100, 3)
vpm = round(100 / (total_time / 60), 1)

print("\n" + "=" * 65)
print("100-VILLAGE LIVE USER BENCHMARK RESULT:")
print(f"Total Villages Processed: 100")
print(f"Successful Villages: {st['completed_count']}")
print(f"Failed Villages: {st['failed_count']}")
print(f"Total Execution Time: {total_time} seconds")
print(f"Average Processing Speed: {avg_time}s / village ({round(avg_time * 1000, 1)} ms)")
print(f"System Throughput: {vpm} villages / minute")
est_2000_seconds = round(2000 * avg_time, 1)
est_2000_minutes = round(est_2000_seconds / 60, 1)
print(f"Projected Time for Full 2,000 Villages: {est_2000_minutes} minutes ({est_2000_seconds}s)")
print("=" * 65)
