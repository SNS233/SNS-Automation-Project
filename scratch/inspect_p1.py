import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})
p = s.get('https://generate.snsies.com/login')
csrf = re.search(r'name="_token"\s+value="([^"]+)"', p.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': csrf, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345'})

# Check the main table (page 1)
r = s.get('https://generate.snsies.com/')
tbody = re.search(r'<tbody[^>]*>(.*?)</tbody>', r.text, re.DOTALL)
if tbody:
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL)
    print(f"Total rows on page 1: {len(rows)}")
    for i, row in enumerate(rows[:10]):
        v_info = re.search(r'<td>(.*?)</td>', row)
        badge = re.search(r'<span class="badge[^>]*>(.*?)</span>', row)
        rev = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', row)
        btn = re.search(r'data-village-id="(\d+)"[^>]*data-village-name="([^"]*)"[^>]*data-mode="([^"]*)"', row)
        b_name = btn.group(2) if btn else ""
        b_mode = btn.group(3) if btn else ""
        b_id = btn.group(1) if btn else ""
        print(f"Row {i+1}: {v_info.group(1) if v_info else ''} | Badge: {badge.group(1) if badge else 'None'} | Rev: {rev.group(1) if rev else 'None'} | Btn: id={b_id}, name={b_name}, mode={b_mode}")
