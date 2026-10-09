import sys
from pathlib import Path
sys.path.insert(0, str(Path('.')))
from services.automation_service import DirectPortalClient

c = DirectPortalClient('https://generate.snsies.com/')
c.login()

for vid in [54, 150, 774, 775, 776, 777]:
    resp = c.session.get(f'https://generate.snsies.com/villages/{vid}/map-data')
    if resp.status_code == 200:
        data = resp.json()
        print(f"Village ID {vid} ({data.get('village')}): status = '{data.get('status')}'")
    else:
        print(f"Village ID {vid}: HTTP {resp.status_code}")
