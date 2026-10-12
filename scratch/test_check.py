import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)
resp = s.get('https://generate.snsies.com/?q=518749')
tables = re.findall(r'<table[^>]*>(.*?)</table>', resp.text, re.DOTALL)
if len(tables) > 1:
    tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', tables[1], re.DOTALL)
    print("Row in Table 1:")
    print(tbody.group(1))
