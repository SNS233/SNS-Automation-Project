import requests

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
import re
csrf = re.search(r'name="_token"\s+value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})

res = s.get('https://generate.snsies.com/villages/19/review')
print('Review page HTTP status:', res.status_code)
print('Review page final URL:', res.url)
print('Page title/h1:', re.findall(r'<h[12][^>]*>(.*?)</h[12]>', res.text))
