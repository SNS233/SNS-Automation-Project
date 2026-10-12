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

test_codes = [
    ("511635", "Huka"),
    ("511910", "Kothadiya"),
    ("511494", "Panar"),
    ("511919", "Parabdi"),
    ("511750", "Vejalka"),
    ("516997", "Bhurakui"),
    ("516890", "Gangapura"),
    ("516994", "Shahpur"),
    ("516979", "Shekhadi"),
    ("510916", "Chumfari")
]

pending_village = None

for code, name in test_codes:
    t0 = time.time()
    resp = s.get(f"https://generate.snsies.com/?q={code}")
    dur = round(time.time() - t0, 3)
    rev = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', resp.text)
    if rev:
        print(f"[{code} {name}] Already REVIEWED in {dur}s: {rev.group(1)}")
    else:
        print(f"[{code} {name}] PENDING in {dur}s!")
        # Extract row info
        btn_match = re.search(r'data-village-id="(\d+)"', resp.text)
        if btn_match:
            print(f"  Found data-village-id: {btn_match.group(1)}")
            pending_village = (code, name, btn_match.group(1))
            break
        else:
            # Print row html
            rows = re.findall(r'<tr[^>]*>.*?</tr>', resp.text, re.DOTALL)
            for r in rows:
                if code in r:
                    print("  Row HTML:", r[:400])

if pending_village:
    code, name, v_id = pending_village
    print(f"\nTesting DIRECT GENERATION for pending village: {name} (Code: {code}, ID: {v_id})...")
    # Get fresh CSRF
    home = s.get("https://generate.snsies.com/")
    c_m = re.search(r'name="csrf-token"\s+content="([^"]+)"', home.text)
    csrf_token = c_m.group(1) if c_m else csrf
    
    t_start = time.time()
    detect_url = f"https://generate.snsies.com/village-words/{v_id}/detect"
    print(f"Posting to: {detect_url}")
    post_res = s.post(detect_url, data={
        '_token': csrf_token,
        'imagery_provider': 'google',
        'use_ai': '0'
    }, allow_redirects=True, timeout=120)
    dur_total = round(time.time() - t_start, 2)
    print(f"Generation completed in {dur_total}s!")
    print(f"Status Code: {post_res.status_code}")
    print(f"Final URL: {post_res.url}")
    print(f"Redirect history: {[r.url for r in post_res.history]}")
