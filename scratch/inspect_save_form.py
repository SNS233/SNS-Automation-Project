import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.automation_service import DirectPortalClient
import re

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

rev = c.session.get('https://generate.snsies.com/villages/54/review')
for f in re.findall(r'<form[^>]*action="([^"]*)"[^>]*>(.*?)</form>', rev.text, re.DOTALL):
    if 'Save review' in f[1]:
        print("ACTION:", f[0])
        print("CONTENT:\n", f[1])
