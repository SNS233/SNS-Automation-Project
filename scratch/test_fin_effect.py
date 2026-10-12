import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

# Check village 150 before finalize
resp1 = s.get('https://generate.snsies.com/villages/150/map-data')
print('150 before finalize:', resp1.json().get('status'), len(resp1.json().get('boundary', {}).get('coordinates', [])))

# Post finalize
token_review = re.search(r'name="_token" value="([^"]+)"', s.get('https://generate.snsies.com/villages/150/review').text).group(1)
res_fin = s.post('https://generate.snsies.com/villages/150/finalize', data={'_token': token_review})
print("Finalize status:", res_fin.status_code)

# Check village 150 after finalize
resp2 = s.get('https://generate.snsies.com/villages/150/map-data')
print('150 after finalize:', resp2.json().get('status'), len(resp2.json().get('boundary', {}).get('coordinates', [])))
