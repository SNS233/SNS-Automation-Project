import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})
res = s.get('https://generate.snsies.com/?q=Aabhva')
rows = re.findall(r'<tr[^>]*>.*?</tr>', res.text, re.DOTALL)
for r in rows:
    if 'Aabhva' in r:
        print('=== FULL AABHVA ROW ===')
        print(r)
