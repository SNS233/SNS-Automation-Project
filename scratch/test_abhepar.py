import requests
import re
import time

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

print("1. Logging in...")
login_page = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={
    '_token': csrf,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
})

print("2. Getting fresh CSRF token from home page...")
p_home = s.get('https://generate.snsies.com/?q=512317')
meta_csrf = re.search(r'<meta name="csrf-token" content="([^"]+)"', p_home.text)
token = meta_csrf.group(1) if meta_csrf else csrf
print(f"   CSRF token: {token}")

print("3. Submitting detect POST for Abhepar (village_id=17290)...")
t0 = time.time()
payload = {
    '_token': token,
    'imagery_provider': 'google',
    'use_ai': '0'
}
resp = s.post('https://generate.snsies.com/village-words/17290/detect', data=payload, timeout=60, allow_redirects=False)
dur = round(time.time() - t0, 3)
print(f"   POST response status: {resp.status_code} in {dur}s")
print(f"   POST headers: {dict(resp.headers)}")
print(f"   POST body preview: {resp.text[:300]}")

if resp.status_code in (301, 302):
    loc = resp.headers.get('Location')
    print(f"   Redirect target: {loc}")
    if loc:
        r_loc = s.get(loc, allow_redirects=True)
        print(f"   Final URL reached: {r_loc.url} (Status: {r_loc.status_code})")

# Also check search result for 512317 now
print("4. Checking search result for 512317...")
chk = s.get('https://generate.snsies.com/?q=512317')
rev = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', chk.text)
badge = re.search(r'<span class="badge[^>]*>(.*?)</span>', chk.text)
del_form = re.search(r'action="(https://generate\.snsies\.com/villages/\d+)"', chk.text)
print(f"   Search Review Link: {rev.group(1) if rev else 'None'}")
print(f"   Search Badge: {badge.group(1) if badge else 'None'}")
print(f"   Search Delete Form: {del_form.group(1) if del_form else 'None'}")
