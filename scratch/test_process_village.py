import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import time
from services.automation_service import DirectPortalClient

client = DirectPortalClient(
    base_url="https://generate.snsies.com",
    username="admin@kmltodata.local",
    password="Admin@12345"
)
ok, msg = client.login()
print(f"Login: ok={ok}, msg={msg}")

# Test Davadra (518753)
print("\n--- Testing Davadra (518753) ---")
res1 = client.process_village(village_name="Davadra", village_code="518753", auto_review_correct=True)
print("Davadra result:", res1['status'], res1['link'], res1.get('duration'), res1.get('message'))

# Test Paroli (518749)
print("\n--- Testing Paroli (518749) ---")
res2 = client.process_village(village_name="Paroli", village_code="518749", auto_review_correct=True)
print("Paroli result:", res2['status'], res2['link'], res2.get('duration'), res2.get('message'))
