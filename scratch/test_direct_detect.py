import requests
import re
import time

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# 1. Login
login_page = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={
    '_token': csrf,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
})

# 2. Get home page to get CSRF token from meta or form
home_resp = s.get('https://generate.snsies.com/?q=511494')
csrf_token = None
meta_m = re.search(r'meta name="csrf-token" content="([^"]+)"', home_resp.text)
if meta_m:
    csrf_token = meta_m.group(1)
else:
    token_m = re.search(r'name="_token"\s+value="([^"]+)"', home_resp.text)
    if token_m:
        csrf_token = token_m.group(1)

print(f"CSRF token: {csrf_token}")

# Check village row
btn_m = re.search(r'data-village-id="(\d+)"', home_resp.text)
if btn_m:
    village_word_id = btn_m.group(1)
    print(f"Found pending village_word_id: {village_word_id}")
    
    # Send detect request
    t0 = time.time()
    payload = {
        '_token': csrf_token,
        'imagery_provider': 'google',
        'use_ai': '0'
    }
    # Note: don't auto follow redirect immediately to observe status code and headers
    detect_resp = s.post(f"https://generate.snsies.com/village-words/{village_word_id}/detect", data=payload, allow_redirects=False)
    print(f"Detect POST status: {detect_resp.status_code}")
    print(f"Detect POST headers: {dict(detect_resp.headers)}")
    print(f"Detect POST response text (first 500 chars): {detect_resp.text[:500]}")
    
    # If 302, where does it redirect?
    if detect_resp.status_code in (301, 302):
        loc = detect_resp.headers.get('Location')
        print(f"Redirect Location: {loc}")
        if loc:
            r2 = s.get(loc, allow_redirects=False)
            print(f"Redirect GET status: {r2.status_code}, Location: {r2.headers.get('Location')}")
    
    # Check ?q=511494 again
    time.sleep(1)
    chk_resp = s.get('https://generate.snsies.com/?q=511494')
    m_rev = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', chk_resp.text)
    print(f"After detect POST check: {m_rev.group(1) if m_rev else 'Still pending or processing'}")
else:
    print("Could not find data-village-id")
