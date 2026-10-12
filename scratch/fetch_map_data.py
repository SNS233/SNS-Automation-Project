import requests
import re
import json

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={
    '_token': token,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
}, allow_redirects=True)

data_resp = s.get('https://generate.snsies.com/villages/156/map-data', headers={'Accept': 'application/json'})
print("Map data status:", data_resp.status_code)
d = data_resp.json()
print("Keys:", list(d.keys()))
print("Counts:", d.get('counts'))
print("Number of wells:", len(d.get('wells', [])))
if d.get('wells'):
    print("Sample well 0:", d['wells'][0])
if 'boundary' in d:
    b = d['boundary']
    print("Boundary type:", type(b), "keys:", list(b.keys()) if isinstance(b, dict) else '')

with open('scratch/map_data_156.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2)

print("Saved scratch/map_data_156.json")
