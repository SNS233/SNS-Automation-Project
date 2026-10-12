import requests
import re
import time

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# 1. Login
t0 = time.time()
login_page = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text).group(1)
resp_login = s.post('https://generate.snsies.com/login', data={
    '_token': csrf,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
}, allow_redirects=True)
print(f"Logged in in {round(time.time() - t0, 2)}s, status: {resp_login.status_code}")

# Extract CSRF token from session
csrf_token = re.search(r'name="csrf-token"\s+content="([^"]+)"', resp_login.text)
if not csrf_token:
    csrf_token = re.search(r'name="_token"\s+value="([^"]+)"', resp_login.text)
token_val = csrf_token.group(1) if csrf_token else csrf
print("Active CSRF Token:", token_val)

# Test Village 1: Bhankoda (511489) - Reviewed
t_v1 = time.time()
q_resp = s.get('https://generate.snsies.com/?q=511489')
dur_search = round(time.time() - t_v1, 2)
# Check for review link in table
review_match = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', q_resp.text)
if review_match:
    print(f"[Village 1 Bhankoda] Found review link in {dur_search}s: {review_match.group(1)}")

# Test Village 2: Let's pick a pending village from user's CSV:
# E.g. Hathipura (511476) or Huka (511635) or Changodar (511624)
test_code = "511476"
t_v2 = time.time()
q2 = s.get(f'https://generate.snsies.com/?q={test_code}')
print(f"Search {test_code} status: {q2.status_code} in {round(time.time() - t_v2, 2)}s")

# Check if review link already exists
rev2 = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', q2.text)
if rev2:
    print(f"Village {test_code} already has review link: {rev2.group(1)}")
else:
    print(f"Village {test_code} does not have review link. Searching for js-open-detect button...")
    # Look for button with data-village-id
    btn_match = re.search(r'class="[^"]*js-open-detect[^"]*"[^>]*data-village-id="(\d+)"[^>]*data-village-name="([^"]*)"', q2.text)
    if not btn_match:
        btn_match = re.search(r'data-village-id="(\d+)"[^>]*class="[^"]*js-open-detect[^"]*"', q2.text)
    
    if btn_match:
        v_id = btn_match.group(1)
        print(f"Found village ID for {test_code}: {v_id}")
        # Test direct POST to the backend detect endpoint
        t_detect = time.time()
        detect_url = f"https://generate.snsies.com/village-words/{v_id}/detect"
        print(f"Triggering direct backend POST to: {detect_url} ...")
        detect_post = s.post(detect_url, data={
            '_token': token_val,
            'imagery_provider': 'google',
            'use_ai': '0'
        }, allow_redirects=True, timeout=120)
        dur_gen = round(time.time() - t_detect, 2)
        print(f"Direct generation POST completed in {dur_gen}s! Status: {detect_post.status_code}")
        print(f"Final URL reached by backend redirect: {detect_post.url}")
        print(f"Response history (redirects): {[r.status_code for r in detect_post.history]}")
    else:
        print("Could not find js-open-detect button in HTML. Row HTML snippet:")
        row_snip = re.search(r'<tr[^>]*>.*?511476.*?</tr>', q2.text, re.DOTALL)
        if row_snip:
            print(row_snip.group(0))
