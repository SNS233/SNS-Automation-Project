from app import create_app
import io
import os
from pathlib import Path

def test_api():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    print("==================================================")
    print("RUNNING API HTTP ENDPOINT TESTS")
    print("==================================================")

    # 1. Test Login Page
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'MASTER BOREWELL PORTAL' in resp.data
    print("[API TEST 1] GET /login -> 200 OK")

    # 2. Test Unauthenticated Redirect
    resp = client.get('/')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']
    print("[API TEST 2] GET / (Unauthenticated) -> 302 Redirect to /login")

    # 3. Test Login Authentication
    resp = client.post('/api/auth/login', json={'username': 'admin', 'password': 'Admin@123'})
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data['success'] is True
    assert json_data['user']['username'] == 'admin'
    print("[API TEST 3] POST /api/auth/login -> 200 OK (Logged in)")

    # 4. Test Authenticated Home Page
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'BOREWELL PORTAL' in resp.data
    print("[API TEST 4] GET / (Authenticated) -> 200 OK")

    # 5. Test Dashboard Metrics Endpoint
    resp = client.get('/api/dashboard/metrics')
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data['success'] is True
    assert 'summary' in json_data['data']
    print(f"[API TEST 5] GET /api/dashboard/metrics -> 200 OK (Total Villages: {json_data['data']['summary']['total_villages']})")

    # 6. Test Villages List Endpoint
    resp = client.get('/api/villages?page=1&page_size=10')
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data['success'] is True
    assert 'items' in json_data['data']
    print(f"[API TEST 6] GET /api/villages -> 200 OK ({len(json_data['data']['items'])} items returned)")

    # 7. Test Automation Status Endpoint (with 5 KPIs)
    resp = client.get('/api/automation/status')
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data['success'] is True
    st = json_data['data']
    assert 'total_villages' in st
    assert 'completed_count' in st
    assert 'processing_count' in st
    assert 'failed_count' in st
    assert 'remaining_count' in st
    print(f"[API TEST 7] GET /api/automation/status -> 200 OK (Status: {st['status']}, Total: {st['total_villages']})")

    # 8. Test Automation Start Endpoint with Gujarati Excel file
    sample_file_path = Path("uploads/excel/1791216784_Botad.xlsx")
    if sample_file_path.exists():
        with open(sample_file_path, 'rb') as f:
            data = {
                'file': (io.BytesIO(f.read()), '1791216784_Botad.xlsx')
            }
            resp = client.post('/api/automation/start', data=data, content_type='multipart/form-data')
            assert resp.status_code in (200, 409)  # 200 or 409 if already running
            json_data = resp.get_json()
            print(f"[API TEST 8] POST /api/automation/start -> {resp.status_code} ({json_data.get('message') or json_data.get('error')})")

    # 9. Test Automation Sample Template Download Endpoint
    resp = client.get('/api/automation/sample-template')
    assert resp.status_code == 200
    assert resp.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    print("[API TEST 9] GET /api/automation/sample-template -> 200 OK")

    print("\n==================================================")
    print("ALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    test_api()
