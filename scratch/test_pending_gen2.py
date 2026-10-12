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
    ("510894", "Patyo"),
    ("510967", "Sardarkhantni Muvadi"),
    ("507435", "Bharadava"),
    ("507910", "Jalana"),
    ("508112", "Jorapura Bhakhar"),
    ("507962", "Kanagar"),
    ("507814", "Tadholi"),
    ("522275", "Debar"),
    ("522522", "Nikoli"),
    ("522190", "Prankad"),
    ("522073", "Thikaria"),
    ("516536", "Hathsani"),
    ("516102", "Nava Rampar"),
    ("520789", "Anandpura"),
    ("520103", "Dabherai"),
    ("520181", "Dharoliya Bhindol"),
    ("520791", "Gola Gamdi"),
    ("520113", "Nana Butiyapura"),
    ("520759", "Samdhi"),
    ("520908", "Sanadhara"),
    ("520523", "Sindhadiya"),
    ("520770", "Surya"),
    ("520154", "Vaddhari")
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
        btn_match = re.search(r'data-village-id="(\d+)"', resp.text)
        if btn_match:
            v_id = btn_match.group(1)
            print(f"  Found data-village-id: {v_id}")
            pending_village = (code, name, v_id)
            break
        else:
            print("  No button with data-village-id. Text preview:", resp.text[resp.text.find(code)-50:resp.text.find(code)+300])

if pending_village:
    code, name, v_id = pending_village
    print(f"\n=======================================================")
    print(f"TESTING DIRECT GENERATION FOR PENDING VILLAGE:")
    print(f"Village: {name} | Code: {code} | Village-Word ID: {v_id}")
    print(f"=======================================================")
    
    home = s.get("https://generate.snsies.com/")
    c_m = re.search(r'name="csrf-token"\s+content="([^"]+)"', home.text)
    csrf_token = c_m.group(1) if c_m else csrf
    
    t_start = time.time()
    detect_url = f"https://generate.snsies.com/village-words/{v_id}/detect"
    print(f"POSTing to: {detect_url}")
    
    # Send the EXACT form post that the portal's #detect-modal submits!
    post_res = s.post(detect_url, data={
        '_token': csrf_token,
        'imagery_provider': 'google',
        'use_ai': '0'
    }, allow_redirects=True, timeout=180)
    
    dur_total = round(time.time() - t_start, 2)
    print(f"Direct generation completed in: {dur_total}s!")
    print(f"HTTP Status: {post_res.status_code}")
    print(f"Final URL: {post_res.url}")
    print(f"Redirects traversed: {[r.url for r in post_res.history]}")
