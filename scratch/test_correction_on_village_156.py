import requests
import re
import json
import math
import cv2
import numpy as np

def test_village_156():
    s = requests.Session()
    login_page = s.get('https://generate.snsies.com/login')
    token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
    s.post('https://generate.snsies.com/login', data={
        '_token': token,
        'email': 'admin@kmltodata.local',
        'password': 'Admin@12345',
        'remember': '1'
    }, allow_redirects=True)

    rev_resp = s.get('https://generate.snsies.com/villages/156/review')
    rev_html = rev_resp.text

    csrf_m = re.search(r'<meta name="csrf-token" content="([^"]+)"', rev_html)
    csrf = csrf_m.group(1) if csrf_m else ''

    geb_box_m = re.search(r'<div class="geb-box">(.*?)</div>\s*</div>', rev_html, re.DOTALL)
    geb_data = {}
    if geb_box_m:
        for row in re.findall(r'<div class="row[^"]*">(.*?)</div>', geb_box_m.group(1), re.DOTALL):
            spans = re.findall(r'<span>(.*?)</span>', row)
            if len(spans) == 2:
                geb_data[spans[0].strip()] = int(spans[1].strip()) if spans[1].strip().isdigit() else spans[1].strip()

    print("GEB Data for 156:", geb_data)

    map_data = s.get('https://generate.snsies.com/villages/156/map-data', headers={'Accept': 'application/json'}).json()
    wells = map_data.get('wells', [])
    print(f"Total detected wells in Davadra: {len(wells)}")
    
    # Download and score first 20 wells
    scored_wells = []
    for i, w in enumerate(wells[:20]):
        img_url = w.get('image')
        score = 0.5
        reasons = []
        is_circular = False
        is_abadi = False
        
        if img_url:
            r = s.get(img_url, timeout=10)
            if r.status_code == 200:
                nparr = np.frombuffer(r.content, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    h, w_px = img.shape[:2]
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                    
                    # 1. Check Abadi / Built-up roof characteristics:
                    # Red/brick/tin roofs have distinct hue and high gradient energy
                    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
                    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
                    grad_mag = np.sqrt(sobelx**2 + sobely**2)
                    mean_grad = np.mean(grad_mag)
                    
                    # Check roof colors (hue 0-15 or 160-180 for terracotta/red, high sat)
                    red_mask = ((hsv[:, :, 0] < 15) | (hsv[:, :, 0] > 165)) & (hsv[:, :, 1] > 70)
                    roof_ratio = np.mean(red_mask)
                    
                    if roof_ratio > 0.15 or (mean_grad > 35 and np.std(gray) > 45):
                        is_abadi = True
                        reasons.append("Residential/roof structure pattern")

                    # 2. Check circular well pit:
                    # Circular gradient / Hough circles in center 120x120
                    ch, cw = h // 2, w_px // 2
                    roi_gray = gray[ch-60:ch+60, cw-60:cw+60]
                    blurred = cv2.GaussianBlur(roi_gray, (7, 7), 1.5)
                    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=15,
                                               param1=45, param2=25, minRadius=6, maxRadius=35)
                    if circles is not None and len(circles[0]) > 0:
                        is_circular = True
                        reasons.append("Circular well pit detected")
                        score += 0.35

                    # Center pit contrast (dug well typically has darker water/shadow pit in center with lighter rim)
                    center_r = 15
                    c_patch = gray[ch-center_r:ch+center_r, cw-center_r:cw+center_r]
                    rim_patch = gray[ch-30:ch+30, cw-30:cw+30]
                    c_mean = np.mean(c_patch)
                    r_mean = np.mean(rim_patch)
                    if r_mean - c_mean > 8:
                        score += 0.2
                        reasons.append("Dark pit center contrast")

                    if is_abadi:
                        score -= 0.5
                        
        scored_wells.append({
            'id': w['id'],
            'code': w['code'],
            'type': w['well_type'],
            'score': round(score, 3),
            'is_circular': is_circular,
            'is_abadi': is_abadi,
            'reasons': reasons
        })

    # Sort scored wells
    scored_wells.sort(key=lambda x: x['score'], reverse=True)
    print("\nTop 5 Scored Wells:")
    for sw in scored_wells[:5]:
        print(sw)
    print("\nBottom 5 Scored Wells:")
    for sw in scored_wells[-5:]:
        print(sw)

if __name__ == '__main__':
    test_village_156()
