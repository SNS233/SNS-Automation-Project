import sys
from pathlib import Path
sys.path.insert(0, str(Path('.')))
from services.automation_service import DirectPortalClient
import re

c = DirectPortalClient('https://generate.snsies.com/')
c.login()
hp = c.session.get('https://generate.snsies.com/')
tables = re.findall(r'<table[^>]*>(.*?)</table>', hp.text, re.DOTALL)
if tables:
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tables[0], re.DOTALL):
        links = re.findall(r'href="([^"]+)"', tr)
        text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' | ', tr)).strip()
        print('ROW:', text, 'LINKS:', links)
