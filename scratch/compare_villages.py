import sys
from pathlib import Path
sys.path.insert(0, str(Path('.')))
from services.automation_service import DirectPortalClient
import json

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

# Village 54 was human-review finalized
m54 = c.session.get('https://generate.snsies.com/villages/54/map-data').json()
# Village 777 was just AI generated, never human reviewed
m777 = c.session.get('https://generate.snsies.com/villages/777/map-data').json()

print("M54 keys:", m54.keys())
print("M54 status:", m54.get('status'), "counts:", m54.get('counts'), "village:", m54.get('village'))
print("M777 status:", m777.get('status'), "counts:", m777.get('counts'), "village:", m777.get('village'))

# Let's check review page HTML differences between 54 and 777
r54 = c.session.get('https://generate.snsies.com/villages/54/review').text
r777 = c.session.get('https://generate.snsies.com/villages/777/review').text

print("\nr54 length:", len(r54), "r777 length:", len(r777))
# Check if there is any date, version, or reviewed indicator
import re
print("54 form action:", re.findall(r'<form[^>]*action="([^"]*)"', r54))
print("777 form action:", re.findall(r'<form[^>]*action="([^"]*)"', r777))
