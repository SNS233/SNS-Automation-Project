import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
resp = s.post('https://generate.snsies.com/login', data={
    '_token': token,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
}, allow_redirects=True)

print("Logged in, final url:", resp.url)

rev = s.get('https://generate.snsies.com/villages/156/review')
print("Review page status:", rev.status_code)

with open('scratch/review_page_156.html', 'w', encoding='utf-8') as f:
    f.write(rev.text)

print("Saved scratch/review_page_156.html, length:", len(rev.text))
