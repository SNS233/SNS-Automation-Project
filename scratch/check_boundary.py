import requests
import re
import json

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

for vid in [156, 150, 651, 652]:
    resp = s.get(f'https://generate.snsies.com/villages/{vid}/map-data', headers={'Accept': 'application/json'})
    print(f"\n=== Village {vid} map-data ===")
    print("Status code:", resp.status_code)
    try:
        data = resp.json()
        print("Keys:", list(data.keys()))
        print("boundary:", data.get('boundary'))
        coords = data.get('boundary', {}).get('coordinates', []) if isinstance(data.get('boundary'), dict) else []
        print(f"boundary coordinates length: {len(coords)}")
        print(f"wells count: {len(data.get('wells', []))}")
    except Exception as e:
        print("Error parsing JSON:", e)
