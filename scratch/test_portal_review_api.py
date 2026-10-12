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

rev_resp = s.get('https://generate.snsies.com/villages/156/review')
rev_html = rev_resp.text

csrf_m = re.search(r'<meta name="csrf-token" content="([^"]+)"', rev_html)
csrf = csrf_m.group(1) if csrf_m else ''
print("CSRF:", csrf)

geb_box_m = re.search(r'<div class="geb-box">(.*?)</div>\s*</div>', rev_html, re.DOTALL)
geb_info = {}
if geb_box_m:
    for row in re.findall(r'<div class="row[^"]*">(.*?)</div>', geb_box_m.group(1), re.DOTALL):
        spans = re.findall(r'<span>(.*?)</span>', row)
        if len(spans) == 2:
            geb_info[spans[0].strip()] = spans[1].strip()

print("Extracted GEB info:", geb_info)

map_data = s.get('https://generate.snsies.com/villages/156/map-data', headers={'Accept': 'application/json'}).json()
wells = map_data.get('wells', [])
print(f"Wells in 156: {len(wells)}")

# Test Add Well
headers = {
    'Content-Type': 'application/json',
    'X-CSRF-TOKEN': csrf,
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
}
add_resp = s.post('https://generate.snsies.com/villages/156/wells', headers=headers, json={'lat': 22.5968, 'lon': 73.7197, 'well_type': 'tube'})
print("Add well response:", add_resp.status_code, add_resp.text)

if add_resp.status_code in (200, 201):
    well_data = add_resp.json()
    new_id = well_data.get('well', {}).get('id') or well_data.get('id')
    print("Created well ID:", new_id)
    if new_id:
        del_headers = {
            'X-CSRF-TOKEN': csrf,
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        del_resp = s.delete(f'https://generate.snsies.com/villages/156/wells/{new_id}', headers=del_headers)
        print("Delete well response:", del_resp.status_code, del_resp.text)

