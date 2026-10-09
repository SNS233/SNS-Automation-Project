import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

for term in ['Davadra', '518753', 'Motal', '518539', 'Vandaria', '521357', 'Aida']:
    r = s.get(f'https://generate.snsies.com/?status=all&q={term}')
    tbody_m = re.search(r'<tbody[^>]*>(.*?)</tbody>', r.text, re.DOTALL)
    print(f"\n--- Search: '{term}' ---")
    if tbody_m:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_m.group(1), re.DOTALL)
        print(f"Total rows: {len(rows)}")
        for r_item in rows[:2]:
            clean = ' '.join(re.sub(r'<[^>]+>', ' ', r_item).split())
            print(f"  {clean[:90]}")
    else:
        print("No tbody")
