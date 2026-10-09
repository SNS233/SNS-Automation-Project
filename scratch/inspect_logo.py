import os
import requests
import re
from PIL import Image

# 1. Check generate.snsies.com for logo
try:
    r = requests.get('https://generate.snsies.com/login')
    imgs = re.findall(r'<img[^>]*src=["\']([^"\']+)["\']', r.text)
    svgs = re.findall(r'<svg[^>]*>.*?</svg>', r.text, re.DOTALL)
    print("generate.snsies.com/login img tags:", imgs)
    print("generate.snsies.com/login svg count:", len(svgs))
except Exception as e:
    print("Error querying remote:", e)

# 2. Check Downloads images for SNS logo
dl_dir = r'C:\Users\Admin\Downloads'
for fname in os.listdir(dl_dir):
    fpath = os.path.join(dl_dir, fname)
    if os.path.isfile(fpath) and fname.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
        try:
            im = Image.open(fpath)
            print(f"File: {fname}, size: {im.size}, format: {im.format}")
        except Exception:
            pass
