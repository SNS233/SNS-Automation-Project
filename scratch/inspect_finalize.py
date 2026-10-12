with open('scratch/review_page_156.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
m = re.search(r'(<form[^>]*action="[^"]*finalize"[^>]*>.*?</form>)', html, re.DOTALL)
if m:
    print(m.group(1))
