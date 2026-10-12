import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})
html = s.get('https://generate.snsies.com/?q=511624').text
js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
if js_blocks:
    with open('scratch/portal_script.js', 'w', encoding='utf-8') as f:
        f.write(js_blocks[0])
    print('Wrote portal_script.js with length:', len(js_blocks[0]))
