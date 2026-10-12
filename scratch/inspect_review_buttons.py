import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.automation_service import DirectPortalClient
import re

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

rev = c.session.get('https://generate.snsies.com/villages/54/review')
print("Review Page buttons and forms:")
for f in re.findall(r'<form[^>]*>(.*?)</form>', rev.text, re.DOTALL):
    print("FORM:", f[:300])

for b in re.findall(r'<button[^>]*>(.*?)</button>', rev.text, re.DOTALL):
    print("BUTTON:", b.strip())

for a in re.findall(r'<a[^>]*class="[^"]*btn[^"]*"[^>]*>(.*?)</a>', rev.text, re.DOTALL):
    print("BTN LINK:", a.strip())
