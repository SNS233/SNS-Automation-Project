import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.automation_service import DirectPortalClient
import re

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

# Let's inspect what happens when finalizing village 54 (Bharkunda)
rev_resp = c.session.get('https://generate.snsies.com/villages/54/review')
token_m = re.search(r'name="_token" value="([^"]+)"', rev_resp.text)
token = token_m.group(1) if token_m else ""

fin_resp = c.session.post('https://generate.snsies.com/villages/54/finalize', data={'_token': token}, allow_redirects=False)
print("Finalize status:", fin_resp.status_code)
print("Finalize headers:", dict(fin_resp.headers))
print("Finalize text snippet:", fin_resp.text[:300])

# Now check review page 54 after finalize
rev_after = c.session.get('https://generate.snsies.com/villages/54/review')
# Check if there is any flash message, banner, or badge in rev_after
alerts = re.findall(r'<div[^>]*class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', rev_after.text, re.DOTALL)
print("Alerts on review page:", alerts)
badges = re.findall(r'<span[^>]*class="[^"]*badge[^"]*"[^>]*>(.*?)</span>', rev_after.text, re.DOTALL)
print("Badges on review page:", badges)

# Also check home page recent villages table
hp = c.session.get('https://generate.snsies.com/')
recent_m = re.search(r'<h3>Recent villages</h3>\s*<table[^>]*>(.*?)</table>', hp.text, re.DOTALL)
if recent_m:
    print("\nRecent villages table on home page:")
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', recent_m.group(1), re.DOTALL)[:6]:
        print("  RECENT:", re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' | ', tr)).strip())
