import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})
r = s.get('https://generate.snsies.com/')

tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', r.text, re.DOTALL)
if tbody:
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL)
    print("ROW 2 HTML:")
    print(rows[1])
