import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

test_codes = [
    ('521357', 'Vandaria'),
    ('934527', 'Vijalpor'),
    ('518600', 'Bamroli Khurd'),
    ('518753', 'Davadra'),
    ('518539', 'Motal')
]

for code, name in test_codes:
    r = s.get(f'https://generate.snsies.com/?q={code}')
    tbody_m = re.search(r'<tbody[^>]*>(.*?)</tbody>', r.text, re.DOTALL)
    print(f"\n=== Code: {code} ({name}) ===")
    if not tbody_m:
        print("  No tbody found")
        continue
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_m.group(1), re.DOTALL)
    print(f"  Rows count in tbody: {len(rows)}")
    for i, row in enumerate(rows):
        clean = ' '.join(re.sub(r'<[^>]+>', ' ', row).split())
        links = re.findall(r'href="([^"]+)"', row)
        actions = re.findall(r'action="([^"]+)"', row)
        print(f"  Row {i}: {clean[:80]} | links={links} | actions={actions}")
