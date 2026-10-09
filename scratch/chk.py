import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'})
r = s.get('https://generate.snsies.com/?q=511494')
print('HTML length:', len(r.text))
m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', r.text)
print('Review match:', m.group(1) if m else None)
btn = re.search(r'data-village-id="(\d+)"', r.text)
print('Btn match:', btn.group(1) if btn else None)
badge = re.search(r'<span class="badge[^>]*>(.*?)</span>', r.text)
print('Badge:', badge.group(1) if badge else None)
