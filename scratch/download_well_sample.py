import requests
import re
from pathlib import Path
from PIL import Image
import io

s = requests.Session()
login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={
    '_token': token,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
}, allow_redirects=True)

map_data = s.get('https://generate.snsies.com/villages/156/map-data', headers={'Accept': 'application/json'}).json()
wells = map_data.get('wells', [])

print(f"Total wells in Davadra: {len(wells)}")
Path('scratch/well_samples').mkdir(parents=True, exist_ok=True)

for i, w in enumerate(wells[:10]):
    img_url = w.get('image')
    if img_url:
        r = s.get(img_url)
        if r.status_code == 200:
            out_file = Path(f"scratch/well_samples/well_{w['id']}_{w['code']}_{w['well_type']}.jpg")
            out_file.write_bytes(r.content)
            img = Image.open(io.BytesIO(r.content))
            print(f"Well {w['id']} ({w['code']}, {w['well_type']}, conf={w.get('confidence')}): size={img.size}, saved {out_file.name}")
