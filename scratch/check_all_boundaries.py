import requests
import re
import json

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

for vid in [150, 151, 152, 155, 156, 157, 159, 160, 161, 162, 650, 651, 652]:
    resp = s.get(f'https://generate.snsies.com/villages/{vid}/map-data', headers={'Accept': 'application/json'})
    if resp.status_code == 200:
        data = resp.json()
        b_coords = data.get('boundary', {}).get('coordinates', []) if isinstance(data.get('boundary'), dict) else []
        v_name = str(data.get('village', 'N/A'))
        print(f"Village {vid:3d} ({v_name:20s}): status={data.get('status', 'N/A'):10s} boundary_pts={len(b_coords):3d} wells={len(data.get('wells', [])):3d}")
    else:
        print(f"Village {vid:3d}: HTTP {resp.status_code}")
