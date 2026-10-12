import requests
import re

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

home = s.get('https://generate.snsies.com/')

print("Forms:")
for f in re.findall(r'<form[^>]*>.*?</form>', home.text, re.DOTALL):
    if 'logout' not in f.lower():
        print(f[:400])

print("\nInputs:")
for inp in re.findall(r'<input[^>]*>', home.text):
    print(inp)
