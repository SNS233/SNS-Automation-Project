import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={
    '_token': token,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
}, allow_redirects=True)

rev_html = s.get('https://generate.snsies.com/villages/156/review').text
csrf = re.search(r'name="csrf-token" content="([^"]+)"', rev_html).group(1)

fin_resp = s.post('https://generate.snsies.com/villages/156/finalize', data={'_token': csrf}, allow_redirects=False)
print("Finalize status:", fin_resp.status_code)
print("Location:", fin_resp.headers.get('Location'))
