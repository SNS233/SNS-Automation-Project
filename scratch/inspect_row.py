import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'})
r = s.get('https://generate.snsies.com/?q=511494')

# Find <tbody>...</tbody>
tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', r.text, re.DOTALL)
if tbody:
    print("TBODY CONTENT:")
    print(tbody.group(1))
else:
    print("No tbody found, checking entire table:")
    table = re.search(r'<table[^>]*>(.*?)</table>', r.text, re.DOTALL)
    if table:
        print(table.group(1)[:2000])
    else:
        print("No table found")
