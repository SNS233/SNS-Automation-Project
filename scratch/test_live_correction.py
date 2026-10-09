import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import requests
import re
from services.review_correction_service import ReviewCorrectionService

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

login_page = s.get('https://generate.snsies.com/login')
token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
s.post('https://generate.snsies.com/login', data={
    '_token': token,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
}, allow_redirects=True)

rcs = ReviewCorrectionService()
result = rcs.review_and_correct_village(s, 'https://generate.snsies.com/villages/156/review')

print("\n" + "="*60)
print("CORRECTION RUN RESULT:")
print("Success:", result.get('success'))
print("Duration:", result.get('duration_seconds'), "s")
print("Initial counts:", result.get('initial_counts'))
print("Final counts:", result.get('final_counts'))
print("Deleted count:", result.get('deleted_count'))
print("Reclassified count:", result.get('reclassified_count'))
print("Adjusted count:", result.get('adjusted_count'))
print("Message:", result.get('message'))
print("="*60)
