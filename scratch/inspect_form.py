import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})
r = s.get('https://generate.snsies.com/')

form_m = re.search(r'<form[^>]*id="detect-modal-form"[^>]*>(.*?)</form>', r.text, re.DOTALL)
if form_m:
    print("MODAL FORM HTML:")
    print(form_m.group(0))
else:
    print("Modal form not found")
