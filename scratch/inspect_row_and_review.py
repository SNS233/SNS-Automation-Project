import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
import re
from services.automation_service import DirectPortalClient

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

r = c.session.get('https://generate.snsies.com/?q=511639')
target_row = c._find_village_row(r.text, '511639', 'Bharkunda')
print("Target row for 511639:")
print(target_row)

rev_page = c.session.get('https://generate.snsies.com/villages/54/review')
print("\nReview page 54 status_code:", rev_page.status_code)
for match in re.finditer(r'<span[^>]*class="[^"]*badge[^"]*"[^>]*>(.*?)</span>', rev_page.text, re.IGNORECASE):
    print("Badge on review page:", match.group(0))

map_data = c.session.get('https://generate.snsies.com/villages/54/map-data').json()
print("Map data 54 status:", map_data.get('status'), "counts:", map_data.get('counts'))
