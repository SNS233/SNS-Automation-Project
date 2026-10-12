import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.automation_service import DirectPortalClient
import re

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

kml_resp = c.session.get('https://generate.snsies.com/villages/150/download/kml')
print("KML download status:", kml_resp.status_code)
print("KML length:", len(kml_resp.content))
print("KML preview:\n", kml_resp.text[:400])
