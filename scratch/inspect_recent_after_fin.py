import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.automation_service import DirectPortalClient
import re

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

# Check home page
hp = c.session.get('https://generate.snsies.com/')
# Find rows in recent villages
recent_m = re.search(r'<h3>Recent villages</h3>\s*<table[^>]*>(.*?)</table>', hp.text, re.DOTALL)
if recent_m:
    print("Recent villages table:")
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', recent_m.group(1), re.DOTALL)[:5]:
        print("  RECENT TR:", re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' | ', tr)).strip())

# Check search for Vandaria
sr = c.session.get('https://generate.snsies.com/?q=Vandaria')
v_row = c._find_village_row(sr.text, '', 'Vandaria')
print("\nTarget row for Vandaria:")
print(v_row)
