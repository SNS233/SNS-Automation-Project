import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})
r = s.get('https://generate.snsies.com/villages/68/review')
print('Status:', r.status_code)
print('Final URL:', r.url)
print('Content length:', len(r.text))
print('Has review elements:', 'review' in r.text.lower())
