import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)
resp = s.get('https://generate.snsies.com/?q=518749')
tables = re.findall(r'<table([^>]*)>', resp.text)
for i, t in enumerate(tables):
    print(f"Table {i} tag attributes: <table{t}>")
