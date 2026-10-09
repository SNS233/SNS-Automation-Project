import cv2
import numpy as np
import glob
from pathlib import Path

for img_path in sorted(glob.glob('scratch/well_samples/*.jpg'))[:5]:
    img = cv2.imread(img_path)
    h, w, c = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Crop central region (where well is supposed to be, say center 60x60 out of 320x320)
    ch, cw = h // 2, w // 2
    r = 30
    center_roi = gray[ch-r:ch+r, cw-r:cw+r]
    surround_roi = gray[ch-2*r:ch+2*r, cw-2*r:cw+2*r]
    
    center_mean = np.mean(center_roi)
    center_std = np.std(center_roi)
    surround_mean = np.mean(surround_roi)
    
    # Check circular features (HoughCircles)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
                               param1=50, param2=30, minRadius=5, maxRadius=40)
    num_circles = len(circles[0]) if circles is not None else 0

    # Color saturation & vegetation index estimate:
    sat_mean = np.mean(hsv[:, :, 1])
    # Excess green index (2*G - R - B)
    b, g, red = cv2.split(img)
    exg = 2.0 * g.astype(float) - red.astype(float) - b.astype(float)
    veg_score = np.mean(exg)

    print(f"{Path(img_path).name}: shape={h}x{w}, center_mean={center_mean:.1f}, std={center_std:.1f}, "
          f"surround_mean={surround_mean:.1f}, circles={num_circles}, sat={sat_mean:.1f}, veg={veg_score:.1f}")
