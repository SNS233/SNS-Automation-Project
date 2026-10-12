import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})

# Check pages 1 to 5 to see what different statuses and buttons look like
for page in range(1, 6):
    r = s.get(f'https://generate.snsies.com/?page={page}')
    matches = re.findall(r'<button[^>]*class="[^"]*js-open-detect[^"]*"[^>]*>(.*?)</button>', r.text)
    btns = re.findall(r'data-village-id="(\d+)"[^>]*data-village-name="([^"]*)"[^>]*data-mode="([^"]*)"', r.text)
    no_bounds = len(re.findall(r'No boundary', r.text))
    reviews = len(re.findall(r'/review', r.text))
    print(f"Page {page}: {len(btns)} detect buttons (modes: {[b[2] for b in btns[:5]]}), {no_bounds} no-boundaries, {reviews} reviews")
