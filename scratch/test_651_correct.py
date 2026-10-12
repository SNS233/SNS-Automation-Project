import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import re
from services.review_correction_service import ReviewCorrectionService

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={'_token': token, 'email': 'admin@kmltodata.local', 'password': 'Admin@12345', 'remember': '1'}, allow_redirects=True)

rcs = ReviewCorrectionService(base_url='https://generate.snsies.com')
excel_hints = {'electric_kuva': 20, 'electric_bor': 5, 'total': 25}
res = rcs.review_and_correct_village(
    session=s,
    review_url='https://generate.snsies.com/villages/150/review',
    excel_hints=excel_hints
)
print("Result of review correction on 150:")
for k, v in res.items():
    if k != 'raw':
        print(f"  {k}: {v}")
