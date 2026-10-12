import requests
import re

s = requests.Session()
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})

for query in ['150', '511639', 'Vandaria']:
    r = s.get(f'https://generate.snsies.com/?q={query}')
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', r.text, re.DOTALL)
    print(f"=== Query: {query} (found {len(rows)} rows) ===")
    for row in rows[:3]:
        clean = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' | ', row)).strip()
        print("  ROW:", clean)
        # Also print raw links / badges
        links = re.findall(r'href="([^"]+)"', row)
        actions = re.findall(r'action="([^"]+)"', row)
        badges = re.findall(r'class="[^"]*badge[^"]*"[^>]*>(.*?)<', row)
        print("  LINKS:", links, "ACTIONS:", actions, "BADGES:", badges)
