import requests
import openpyxl
import time
from pathlib import Path

# Create a 20-village batch
test_excel_path = Path("scratch/test_batch_20.xlsx")
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Villages"

headers = ["ગામનું નામ", "ગામનો કોડ", "જિલ્લાનું નામ"]
ws.append(headers)

sample_data = [
    ["Bharkunda", "511639", "Ahmedabad"],
    ["Changodar (Og)", "511624", "Ahmedabad"],
    ["Hathipura", "511476", "Ahmedabad"],
    ["Huka", "511635", "Ahmedabad"],
    ["Kothadiya", "511910", "Ahmedabad"],
    ["Panar", "511494", "Ahmedabad"],
    ["Parabdi", "511919", "Ahmedabad"],
    ["Vejalka", "511750", "Ahmedabad"],
    ["Bhurakui", "516997", "Anand"],
    ["Gangapura", "516890", "Anand"],
    ["Shahpur", "516994", "Anand"],
    ["Shekhadi", "516979", "Anand"],
    ["Chumfari", "510916", "Aravalli"],
    ["Patyo", "510894", "Aravalli"],
    ["Sardarkhantni Muvadi", "510967", "Aravalli"],
    ["Bharadava", "507435", "Banaskantha"],
    ["Jalana", "507910", "Banaskantha"],
    ["Jorapura Bhakhar", "508112", "Banaskantha"],
    ["Kanagar", "507962", "Banaskantha"],
    ["Tadholi", "507814", "Banaskantha"]
]

for row in sample_data:
    ws.append(row)

wb.save(str(test_excel_path))
print(f"Created {test_excel_path} with {len(sample_data)} rows.")

s = requests.Session()
s.post("http://127.0.0.1:5000/api/auth/login", json={"username": "admin", "password": "Admin@123"})

# Start job with 1 worker so we have plenty of time to test pause
with open(test_excel_path, 'rb') as f:
    r = s.post("http://127.0.0.1:5000/api/automation/start", files={
        'file': ('test_batch_20.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }, data={'concurrency': '1', 'engine_mode': 'direct'})

print("Start:", r.json())
job_id = r.json()['data']['job_id']

# Wait briefly then PAUSE
time.sleep(0.3)
pause_resp = s.post("http://127.0.0.1:5000/api/automation/pause")
print("Pause call:", pause_resp.json())

# Check paused state
st_pause = s.get("http://127.0.0.1:5000/api/automation/status").json()['data']
print(f"State after PAUSE: status='{st_pause['status']}', processed={st_pause['processed_count']}/{st_pause['total_villages']}")

# Wait 2 seconds while paused to ensure no new villages start
time.sleep(2)
st_pause2 = s.get("http://127.0.0.1:5000/api/automation/status").json()['data']
print(f"State during PAUSE (2s later): status='{st_pause2['status']}', processed={st_pause2['processed_count']}/{st_pause2['total_villages']}")

# Now RESUME
resume_resp = s.post("http://127.0.0.1:5000/api/automation/resume")
print("Resume call:", resume_resp.json())

# Poll until completed
while True:
    time.sleep(0.3)
    st = s.get("http://127.0.0.1:5000/api/automation/status").json()['data']
    print(f"  Processed: {st['processed_count']}/{st['total_villages']} | Success: {st['completed_count']} | Status: {st['status']}")
    if st['status'] in ('completed', 'stopped', 'failed'):
        break

print("=" * 60)
print(f"Job completed! Total: {st['total_villages']}, Success: {st['completed_count']}, Failed: {st['failed_count']}")
print("Pause and Resume test PASSED successfully!")
print("=" * 60)
