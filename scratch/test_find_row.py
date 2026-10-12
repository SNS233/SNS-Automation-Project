import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import re
import time
from services.automation_service import DirectPortalClient

client = DirectPortalClient(base_url="https://generate.snsies.com", username="admin@kmltodata.local", password="Admin@12345")
ok, msg = client.login()
print(f"Login: ok={ok}, msg={msg}")

# Search for Jorapura (Davadra) (518752)
html = client.session.get("https://generate.snsies.com/?q=518752").text

def find_village_row(html, v_code="", v_name=""):
    v_code_str = str(v_code or "").strip()
    v_name_str = str(v_name or "").strip()

    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    if not tables:
        return None

    main_table = None
    for t in tables:
        if re.search(r'<th[^>]*>.*?(?:Sub-district|Status|Actions|GEB Data).*?</th>', t, re.DOTALL | re.IGNORECASE):
            main_table = t
            break
    
    if not main_table:
        main_table = tables[-1]

    tbody_m = re.search(r'<tbody[^>]*>(.*?)</tbody>', main_table, re.DOTALL)
    if not tbody_m:
        return None

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_m.group(1), re.DOTALL)
    if not rows:
        return None

    if v_code_str:
        for r in rows:
            if f"({v_code_str})" in r or f">{v_code_str}<" in r or f'"{v_code_str}"' in r or v_code_str in r:
                return r

    if v_name_str:
        v_name_clean = re.escape(v_name_str.lower())
        for r in rows:
            r_clean = re.sub(r'<[^>]+>', ' ', r).lower()
            if re.search(r'\b' + v_name_clean + r'\b', r_clean) or v_name_str.lower() in r_clean:
                return r

    if len(rows) == 1 and 'No villages found' not in rows[0] and 'No records' not in rows[0]:
        return rows[0]

    return None

row = find_village_row(html, "518752", "Jorapura (Davadra)")
print("Found row for 518752:")
print(' '.join(re.sub(r'<[^>]+>', ' ', row).split()) if row else "None")
