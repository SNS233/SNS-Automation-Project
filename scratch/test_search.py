import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

codes = ['518753', '518749', '518752', '518754']
for c in codes:
    resp = s.get(f'https://generate.snsies.com/?q={c}')
    tables = re.findall(r'<table[^>]*>(.*?)</table>', resp.text, re.DOTALL)
    print(f'=== Search Code: {c} ===')
    if len(tables) > 1:
        # Table 1 is the main table
        tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', tables[1], re.DOTALL)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL) if tbody else []
        print(f'Table 1 rows ({len(rows)}):')
        for r in rows:
            print('  ', ' '.join(re.sub(r'<[^>]+>', ' ', r).split())[:120])
            links = re.findall(r'href="[^"]+"', r)
            btns = re.findall(r'data-village-id="\d+"', r)
            acts = re.findall(r'action="[^"]+"', r)
            print('    links:', links, 'btns:', btns, 'acts:', acts)
    elif len(tables) == 1:
        tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', tables[0], re.DOTALL)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL) if tbody else []
        print(f'Table 0 rows ({len(rows)}):')
        for r in rows:
            print('  ', ' '.join(re.sub(r'<[^>]+>', ' ', r).split())[:120])
    else:
        print('No tables found')
