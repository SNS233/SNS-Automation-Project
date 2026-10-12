import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

for vid in [156, 150, 651, 652]:
    resp = s.get(f'https://generate.snsies.com/villages/{vid}/download/kml')
    print(f"\n=== Village {vid} KML ===")
    print("Status code:", resp.status_code)
    print("Length:", len(resp.text))
    has_poly = '<Polygon>' in resp.text
    has_coords = '<coordinates>' in resp.text
    print(f"Has Polygon: {has_poly}, Has coordinates: {has_coords}")
    if has_poly:
        m = re.search(r'<Polygon>(.*?)</Polygon>', resp.text, re.DOTALL)
        if m:
            print("Polygon snippet:", m.group(1)[:200])
