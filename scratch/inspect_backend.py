import requests
import re
import json

s = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
s.headers.update(headers)

login_page = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text)
csrf_token = csrf.group(1) if csrf else ''
print('CSRF token:', csrf_token)

login_resp = s.post('https://generate.snsies.com/login', data={
    '_token': csrf_token,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
}, allow_redirects=True)
print('Login status:', login_resp.status_code, 'Final URL:', login_resp.url)

# Search for Changodar 511624
q_resp = s.get('https://generate.snsies.com/?q=511624')
print('Search 511624 status:', q_resp.status_code)
html = q_resp.text

# Extract table rows
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
print('Found table rows:', len(rows))
for idx, r in enumerate(rows):
    if '511624' in r or 'Changodar' in r or 'changodar' in r:
        print(f'=== MATCHING ROW {idx} ===')
        print(r)

# Extract detect-modal
modal_match = re.search(r'(<div[^>]*id="detect-modal"[^>]*>.*?</div>\s*</div>\s*</div>)', html, re.DOTALL)
if modal_match:
    print('=== DETECT MODAL ===')
    print(modal_match.group(1)[:2000])
else:
    # search for detect-modal tag
    idx_m = html.find('detect-modal')
    if idx_m != -1:
        print('=== DETECT MODAL SNIPPET ===')
        print(html[idx_m-100:idx_m+1500])

# Extract all forms
forms = re.findall(r'(<form[^>]*>.*?</form>)', html, re.DOTALL)
print('Found forms:', len(forms))
for idx, f in enumerate(forms):
    print(f'=== FORM {idx} ===')
    print(f[:1000])

# Look for JavaScript handling detect-modal or buttons
js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print('Found script blocks:', len(js_blocks))
for idx, js in enumerate(js_blocks):
    if 'detect' in js or 'modal' in js or 'generate' in js or 'fetch' in js or 'ajax' in js:
        print(f'=== SCRIPT BLOCK {idx} ===')
        print(js[:2500])
