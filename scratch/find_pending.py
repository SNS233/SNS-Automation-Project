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

# Let's inspect the main village list page without query to see which villages are currently listed and their status
home_resp = s.get('https://generate.snsies.com/')
print('Home page status:', home_resp.status_code)

# Find rows on the first page
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', home_resp.text, re.DOTALL)
print(f'Total rows on main page: {len(rows)}')
for idx, r in enumerate(rows[:10]):
    has_rev = 'href="https://generate.snsies.com/villages/' in r
    btn = re.search(r'class="[^"]*js-open-detect[^"]*"[^>]*data-village-id="(\d+)"[^>]*data-village-name="([^"]*)"[^>]*data-mode="([^"]*)"', r)
    print(f"Row {idx}: has_review={has_rev}, btn={btn.groups() if btn else None}")

# Now let's test a search with an un-generated code, e.g. Dabhava 519661, Dantiya 519231, etc.
more_codes = [
    ("519661", "Dabhava"),
    ("519231", "Dantiya"),
    ("519152", "Kadvana Pad"),
    ("519641", "Khajuri"),
    ("519654", "Kotambi"),
    ("519534", "Koyada"),
    ("519192", "Lilva Thakor"),
    ("519498", "Nalwai"),
    ("519000", "Piplara"),
    ("522624", "Barda(Khambhla Saja)"),
    ("522803", "Daguniya"),
    ("522682", "Dodipada"),
    ("522625", "Khajurna"),
    ("522744", "Morzira"),
    ("908762", "Udepur"),
    ("511218", "Khata Amba"),
    ("511306", "Sugad (Og)")
]

pending = []
for c, n in more_codes:
    res = s.get(f'https://generate.snsies.com/?q={c}')
    rev = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', res.text)
    if rev:
        print(f"  [{c} {n}] Review URL: {rev.group(1)}")
    else:
        btn = re.search(r'data-village-id="(\d+)"', res.text)
        vid = btn.group(1) if btn else None
        print(f"  [{c} {n}] PENDING! village_word_id = {vid}")
        pending.append((c, n, vid))

print(f"\nTotal Pending found: {len(pending)}")
if pending:
    c, n, vid = pending[0]
    print(f"\n--> TESTING DIRECT POST GENERATION ON PENDING VILLAGE: {n} ({c}, ID {vid}) <--")
    t0 = time.time()
    c_m = re.search(r'name="csrf-token"\s+content="([^"]+)"', home_resp.text)
    csrf_token = c_m.group(1) if c_m else csrf
    
    detect_url = f"https://generate.snsies.com/village-words/{vid}/detect"
    gen_resp = s.post(detect_url, data={
        '_token': csrf_token,
        'imagery_provider': 'google',
        'use_ai': '0'
    }, allow_redirects=True, timeout=120)
    dur = round(time.time() - t0, 2)
    print(f"Direct generation took: {dur}s")
    print(f"HTTP Status: {gen_resp.status_code}")
    print(f"Final URL: {gen_resp.url}")
