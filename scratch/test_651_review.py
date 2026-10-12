import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

resp = s.get('https://generate.snsies.com/villages/651/review')
print("Status code:", resp.status_code)
geb_dug = re.search(r'GEB Dugwell:\s*(\d+)', resp.text)
geb_tube = re.search(r'GEB Tubewell:\s*(\d+)', resp.text)
print("GEB Dugwell:", geb_dug.groups() if geb_dug else "None")
print("GEB Tubewell:", geb_tube.groups() if geb_tube else "None")
