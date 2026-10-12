import requests
import re
import time

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

# Search for 518749
resp = s.get('https://generate.snsies.com/?q=518749')
token_csrf = re.search(r'name="_token" value="([^"]+)"', resp.text)
csrf = token_csrf.group(1) if token_csrf else token

btn_m = re.search(r'data-village-id="(\d+)"', resp.text)
print("Button match:", btn_m.groups() if btn_m else "None")

if btn_m:
    vw_id = btn_m.group(1)
    detect_url = f"https://generate.snsies.com/village-words/{vw_id}/detect"
    print(f"Triggering detect POST to {detect_url}")
    post_resp = s.post(detect_url, data={'_token': csrf, 'imagery_provider': 'google', 'use_ai': '0'}, allow_redirects=False, timeout=60)
    print("Status code:", post_resp.status_code)
    print("Location:", post_resp.headers.get('Location'))

for i in range(10):
    time.sleep(2)
    resp = s.get('https://generate.snsies.com/?q=518749')
    tables = re.findall(r'<table[^>]*>(.*?)</table>', resp.text, re.DOTALL)
    if len(tables) > 1:
        tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', tables[1], re.DOTALL)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL) if tbody else []
        for r in rows:
            txt = ' '.join(re.sub(r'<[^>]+>', ' ', r).split())[:120]
            links = re.findall(r'href="[^"]+"', r)
            btns = re.findall(r'data-village-id="\d+"', r)
            acts = re.findall(r'action="[^"]+"', r)
            print(f"Poll {i}: {txt} | links={links} | btns={btns} | acts={acts}")
            if any('/review' in l for l in links):
                print("FOUND REVIEW LINK!")
                break
    else:
        print(f"Poll {i}: len(tables) = {len(tables)}")
