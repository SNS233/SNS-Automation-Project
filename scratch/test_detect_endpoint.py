import requests
import re
import time

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

login_page = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={
    '_token': csrf,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
})

home_resp = s.get('https://generate.snsies.com/')
c_m = re.search(r'name="csrf-token"\s+content="([^"]+)"', home_resp.text)
csrf_token = c_m.group(1) if c_m else csrf

# Let's inspect Row 3 and Row 6 from home page
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', home_resp.text, re.DOTALL)
for r in rows:
    btn = re.search(r'class="[^"]*js-open-detect[^"]*"[^>]*data-village-id="(\d+)"[^>]*data-village-name="([^"]*)"[^>]*data-mode="([^"]*)"', r)
    if btn:
        vid, vname, mode = btn.groups()
        has_rev = 'href="https://generate.snsies.com/villages/' in r
        print(f"Village {vname} (ID {vid}, mode {mode}): has_review = {has_rev}")
        if not has_rev:
            print(f"\n--> POSTing to https://generate.snsies.com/village-words/{vid}/detect <--")
            t0 = time.time()
            post_res = s.post(f"https://generate.snsies.com/village-words/{vid}/detect", data={
                '_token': csrf_token,
                'imagery_provider': 'google',
                'use_ai': '0'
            }, allow_redirects=True, timeout=120)
            dur = round(time.time() - t0, 2)
            print(f"Completed in {dur}s! HTTP Status: {post_res.status_code}")
            print(f"Final URL: {post_res.url}")
            print(f"History: {[h.url for h in post_res.history]}")
            break
