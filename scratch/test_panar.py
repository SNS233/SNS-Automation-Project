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

# Get fresh CSRF token from home page
home_resp = s.get('https://generate.snsies.com/')
c_m = re.search(r'name="csrf-token"\s+content="([^"]+)"', home_resp.text)
csrf_token = c_m.group(1) if c_m else csrf

print(f"Triggering generation for Panar (Village Code 511494, ID 163)...")
t0 = time.time()
detect_url = "https://generate.snsies.com/village-words/163/detect"
try:
    post_res = s.post(detect_url, data={
        '_token': csrf_token,
        'imagery_provider': 'google',
        'use_ai': '0'
    }, allow_redirects=True, timeout=60)
    dur = round(time.time() - t0, 2)
    print(f"POST returned in {dur}s, HTTP Status: {post_res.status_code}")
    print(f"Final URL: {post_res.url}")
except Exception as e:
    print(f"POST notice: {e}. Checking if village row was updated on portal...")
    time.sleep(2)
    check_r = s.get("https://generate.snsies.com/?q=511494")
    m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', check_r.text)
    if m:
        print(f"RECOVERY SUCCESS: Captured Review URL: {m.group(1)}")
    else:
        print("Still pending or processing. Row snippet:")
        for l in check_r.text.splitlines():
            if '511494' in l or 'Panar' in l or 'processing' in l or 'villages/' in l:
                print(" ", l[:200])
