import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.automation_service import DirectPortalClient

client = DirectPortalClient(
    base_url="https://generate.snsies.com",
    username="admin@kmltodata.local",
    password="Admin@12345"
)
ok, msg = client.login()
print(f"Login: ok={ok}, msg={msg}")

# Test Jorapura (Davadra) (518752) - ungenerated / pending detection
print("\n--- Testing Jorapura (Davadra) (518752) ---")
res = client.process_village(
    village_name="Jorapura (Davadra)",
    village_code="518752",
    auto_review_correct=True,
    max_wait_seconds=180
)
print("Jorapura result:")
for k, v in res.items():
    if k != 'correction_details':
        print(f"  {k}: {v}")
