import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})
r = s.get('https://generate.snsies.com/?q=511639')

tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', r.text, re.DOTALL)
if tbody:
    print("TBODY CONTENT FOR 511639 (Bharkunda):")
    print(tbody.group(1))
