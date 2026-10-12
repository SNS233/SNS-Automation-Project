import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

home = s.get('https://generate.snsies.com/')

# Check pagination or total records
print("Home page status:", home.status_code)
for line in home.text.split('\n'):
    if any(k in line.lower() for k in ['pagination', 'page', 'showing', 'records', 'total', 'entries', 'count']):
        print("  PAGINATION/INFO:", line.strip()[:100])

# Check scripts
for s_code in re.findall(r'<script[^>]*>(.*?)</script>', home.text, re.DOTALL):
    for l in s_code.split('\n'):
        if any(k in l.lower() for k in ['filter', 'search', 'fetch', 'url', 'param']):
            print("  JS:", l.strip()[:100])
