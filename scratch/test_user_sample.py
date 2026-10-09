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

# Sample 30 codes from user's prompt text
user_codes = [
    ("511624", "Changodar (Og)"),
    ("511476", "Hathipura"),
    ("511635", "Huka"),
    ("511910", "Kothadiya"),
    ("511494", "Panar"),
    ("511919", "Parabdi"),
    ("511750", "Vejalka"),
    ("516997", "Bhurakui"),
    ("516890", "Gangapura"),
    ("516994", "Shahpur"),
    ("516979", "Shekhadi"),
    ("510916", "Chumfari"),
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
    ("520113", "Nana Butiyapura")
]

print(f"Testing {len(user_codes)} villages via Direct HTTP...")
t_start = time.time()
found_review = 0
found_pending = 0
not_found = 0

for code, name in user_codes:
    t_v = time.time()
    r = s.get(f"https://generate.snsies.com/?q={code}")
    dur = round((time.time() - t_v) * 1000, 1)
    
    m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', r.text)
    if m:
        found_review += 1
        print(f"[{code}] {name} -> SUCCESS in {dur}ms: {m.group(1)}")
    else:
        btn = re.search(r'data-village-id="(\d+)"', r.text)
        if btn:
            found_pending += 1
            print(f"[{code}] {name} -> PENDING in {dur}ms (ID: {btn.group(1)})")
        else:
            not_found += 1
            print(f"[{code}] {name} -> NOT FOUND in {dur}ms")

total_dur = round(time.time() - t_start, 2)
avg_dur = round(total_dur / len(user_codes), 3)
print("=" * 60)
print(f"Processed {len(user_codes)} villages in {total_dur}s!")
print(f"Average time per village: {avg_dur}s ({round(avg_dur*1000, 1)} ms)")
print(f"Effective Throughput: {round(60/avg_dur, 1)} villages/minute")
print(f"Found Reviewed: {found_review} | Pending: {found_pending} | Not Found: {not_found}")
print("=" * 60)
