import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

# Test 1: Full query parameters like browser form
r1 = s.get('https://generate.snsies.com/?district_id=&sub_district_id=&status=all&q=518753&dug_min=&dug_max=')
tbody_m1 = re.search(r'<tbody[^>]*>(.*?)</tbody>', r1.text, re.DOTALL)
if tbody_m1:
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_m1.group(1), re.DOTALL)
    print(f"Test 1 (full params 518753) rows: {len(rows)}")
    for r in rows:
        print("  Row:", ' '.join(re.sub(r'<[^>]+>', ' ', r).split())[:90])

# Test 2: Search by name 'Davadra'
r2 = s.get('https://generate.snsies.com/?district_id=&sub_district_id=&status=all&q=Davadra&dug_min=&dug_max=')
tbody_m2 = re.search(r'<tbody[^>]*>(.*?)</tbody>', r2.text, re.DOTALL)
if tbody_m2:
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_m2.group(1), re.DOTALL)
    print(f"\nTest 2 (name Davadra) rows: {len(rows)}")
    for r in rows:
        print("  Row:", ' '.join(re.sub(r'<[^>]+>', ' ', r).split())[:90])
