import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import re
from services.automation_service import DirectPortalClient

client = DirectPortalClient(
    base_url="https://generate.snsies.com",
    username="admin@kmltodata.local",
    password="Admin@12345"
)
ok, msg = client.login()
print(f"Login: ok={ok}")

villages = [
    ("Vandaria", "521357"),
    ("Vijalpor", "934527"),
    ("Bamroli Khurd", "518600"),
    ("Davadra", "518753"),
    ("Ghogha", "518782"),
    ("Jaban", "518950"),
    ("Jimiyapura", "518910"),
    ("Mekhar", "518505"),
    ("Mota Chadva", "518886"),
    ("Motal", "518539"),
]

for name, code in villages:
    resp = client.session.get(f"https://generate.snsies.com/?q={code}")
    row = client._find_village_row(resp.text, code, name)
    if not row:
        resp = client.session.get(f"https://generate.snsies.com/?q={name}")
        row = client._find_village_row(resp.text, code, name)
    
    if row:
        rev_m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', row)
        rev_url = rev_m.group(1) if rev_m else "no-review-url"
        status_m = re.search(r'<span class="badge[^"]*">([^<]+)</span>', row)
        st = status_m.group(1) if status_m else "no-badge"
        print(f"[{code}] {name:15} | status={st:9} | url={rev_url}")
    else:
        print(f"[{code}] {name:15} | NOT FOUND ON PORTAL")
