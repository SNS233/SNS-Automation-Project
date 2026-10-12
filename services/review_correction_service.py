import re
import time
import math
import logging
import concurrent.futures
import cv2
import numpy as np
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

class ReviewCorrectionService:
    """
    Automated Human Review & Marking Correction Service for https://generate.snsies.com/
    
    Implements:
    - Step 1: Verification of generation completion & opening review page
    - Step 2: Computer Vision & Geospatial analysis of detected well patches:
        * Abadi / residential / settlement / built-up exclusion
        * Dug well circular pit & rim detection in agricultural fields
        * Tube well / borewell field-edge & pump structure detection
        * Filter non-well artifacts (houses, roofs, shadows, trees, tanks)
        * No guessing / low-confidence rejection
    - Step 3: Portal Human Review controls execution (Delete, Add, Adjust, Reclassify)
    - Step 4: GEB Data target & sanity check validation
    - Step 5: Save review & rebuild KML (Finalize)
    """

    def __init__(self, base_url="https://generate.snsies.com"):
        self.base_url = str(base_url or "https://generate.snsies.com").rstrip('/')

    @staticmethod
    def extract_village_id(url_or_str):
        """Extract numeric village record ID from a review or village URL."""
        if not url_or_str:
            return None
        m = re.search(r'/villages/(\d+)', str(url_or_str))
        return int(m.group(1)) if m else None

    def parse_review_page(self, session, village_id):
        """Fetch review page HTML and extract CSRF token and right-side GEB Data box."""
        url = f"{self.base_url}/villages/{village_id}/review"
        resp = session.get(url, timeout=12)
        if resp.status_code != 200:
            return None, f"Review page returned HTTP {resp.status_code}"
        
        html = resp.text
        csrf_m = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        if not csrf_m:
            csrf_m = re.search(r'name="_token"\s+value="([^"]+)"', html)
        csrf = csrf_m.group(1) if csrf_m else ""

        # Extract GEB Box data
        geb_data = {
            'total_geb': 0,
            'geb_dugwell': 0,
            'geb_tubewell': 0,
            'mi6_dugwell': 0,
            'mi6_tubewell': 0,
            'raw_labels': {}
        }

        geb_box_m = re.search(r'<div class="geb-box">(.*?)</div>\s*</div>', html, re.DOTALL)
        if geb_box_m:
            rows = re.findall(r'<div class="row[^"]*">(.*?)</div>', geb_box_m.group(1), re.DOTALL)
            for r in rows:
                spans = re.findall(r'<span>(.*?)</span>', r)
                if len(spans) == 2:
                    k, v = spans[0].strip(), spans[1].strip()
                    geb_data['raw_labels'][k] = v
                    val_int = int(v) if v.isdigit() else 0
                    k_lower = k.lower()
                    if 'total' in k_lower:
                        geb_data['total_geb'] = val_int
                    elif 'geb' in k_lower and 'dug' in k_lower:
                        geb_data['geb_dugwell'] = val_int
                    elif 'geb' in k_lower and ('tube' in k_lower or 'bore' in k_lower):
                        geb_data['geb_tubewell'] = val_int
                    elif 'mi' in k_lower and 'dug' in k_lower:
                        geb_data['mi6_dugwell'] = val_int
                    elif 'mi' in k_lower and ('tube' in k_lower or 'bore' in k_lower):
                        geb_data['mi6_tubewell'] = val_int

        return {
            'csrf': csrf,
            'geb_data': geb_data,
            'html': html,
            'review_url': url
        }, None

    def fetch_map_data(self, session, village_id):
        """Fetch JSON map data containing existing wells, counts, and village boundary."""
        url = f"{self.base_url}/villages/{village_id}/map-data"
        resp = session.get(url, headers={'Accept': 'application/json'}, timeout=12)
        if resp.status_code != 200:
            return None, f"Map data returned HTTP {resp.status_code}"
        try:
            data = resp.json()
            return data, None
        except Exception as e:
            return None, f"Error decoding map data JSON: {e}"

    def analyze_well_patch(self, session, well_item):
        """
        Analyze a detected well patch image using Computer Vision & Geospatial heuristics:
        1. Abadi / Residential / Roof structure check (EXCLUSION)
        2. Agricultural context check (vegetation, bare soil, field texture)
        3. Dug well circular pit & rim check (open well geometry)
        4. Tube well field-edge / pump shelter / compact signature check
        5. Position shift detection (center offset dx, dy)
        """
        img_url = well_item.get('image')
        res = {
            'id': well_item['id'],
            'code': well_item.get('code', ''),
            'current_type': well_item.get('well_type', 'dug'),
            'lat': float(well_item.get('lat', 0)),
            'lon': float(well_item.get('lon', 0)),
            'initial_conf': float(well_item.get('confidence', 0.5)),
            'source': well_item.get('source', ''),
            'is_valid': True,
            'recommended_type': well_item.get('well_type', 'dug'),
            'validity_score': 0.5,
            'is_abadi': False,
            'is_circular_dug': False,
            'is_field_tubewell': False,
            'offset_px': (0, 0),
            'needs_adjust': False,
            'notes': []
        }

        if not img_url:
            res['validity_score'] = 0.4
            return res

        try:
            r = session.get(img_url, timeout=8)
            if r.status_code != 200 or not r.content:
                res['validity_score'] = 0.4
                return res

            nparr = np.frombuffer(r.content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return res

            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            ch, cw = h // 2, w // 2

            # -------------------------------------------------------------
            # 1. ABADI / RESIDENTIAL / BUILT-UP EXCLUSION CHECK
            # Houses have sharp rectilinear roof edges, high gradient energy,
            # reddish/tin roof colors, and clustered high variance.
            # -------------------------------------------------------------
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            grad_mag = np.sqrt(sobelx**2 + sobely**2)
            mean_grad = float(np.mean(grad_mag))
            std_gray = float(np.std(gray))

            # Roof color masks: terracotta/red roofs (hue 0-15 or 160-180 with moderate sat)
            roof_mask = (((hsv[:, :, 0] < 16) | (hsv[:, :, 0] > 165)) & (hsv[:, :, 1] > 60) & (hsv[:, :, 2] > 70))
            roof_ratio = float(np.mean(roof_mask))

            # White/bright tin roofs or concrete slabs
            bright_slab = float(np.mean((hsv[:, :, 1] < 30) & (hsv[:, :, 2] > 210)))

            if roof_ratio > 0.16 or bright_slab > 0.22 or (mean_grad > 38 and std_gray > 48):
                res['is_abadi'] = True
                res['notes'].append("Dense built-up / residential structure pattern (Abadi exclusion)")

            # -------------------------------------------------------------
            # 2. AGRICULTURAL CONTEXT CHECK
            # Gujarat fields: vegetation (excess green), bare agricultural soil,
            # or field boundary bunds.
            # -------------------------------------------------------------
            b, g, red = cv2.split(img)
            exg = 2.0 * g.astype(float) - red.astype(float) - b.astype(float)
            veg_score = float(np.mean(exg))
            mean_sat = float(np.mean(hsv[:, :, 1]))

            has_agri_context = (veg_score > -15.0 or (mean_sat > 70 and not res['is_abadi']))

            # -------------------------------------------------------------
            # 3. DUG WELL ANALYSIS (Circular pit + masonry rim)
            # -------------------------------------------------------------
            # Crop central region (where well is centered, 120x120)
            roi_size = 60
            roi_gray = gray[max(0, ch - roi_size):min(h, ch + roi_size), max(0, cw - roi_size):min(w, cw + roi_size)]
            blurred = cv2.GaussianBlur(roi_gray, (7, 7), 1.5)

            circles = cv2.HoughCircles(
                blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=18,
                param1=45, param2=26, minRadius=6, maxRadius=38
            )

            pit_detected = False
            best_center_offset = (0, 0)

            if circles is not None and len(circles[0]) > 0:
                # Find circle closest to patch center
                best_c = None
                best_dist = 999.0
                roi_ch, roi_cw = roi_gray.shape[0] // 2, roi_gray.shape[1] // 2
                for c in circles[0]:
                    cx, cy, cr = float(c[0]), float(c[1]), float(c[2])
                    dist = math.hypot(cx - roi_cw, cy - roi_ch)
                    if dist < best_dist and dist < 35:
                        best_dist = dist
                        best_c = (cx, cy, cr)

                if best_c is not None:
                    pit_detected = True
                    res['is_circular_dug'] = True
                    res['notes'].append(f"Circular pit detected (r={best_c[2]:.1f}px)")
                    # Offset from image center
                    dx = best_c[0] - roi_cw
                    dy = best_c[1] - roi_ch
                    best_center_offset = (dx, dy)
                    if math.hypot(dx, dy) > 4.5:
                        res['needs_adjust'] = True
                        res['offset_px'] = (dx, dy)

            # Center pit vs rim contrast: Dug wells have darker center pit (water/shadow) surrounded by lighter rim
            center_r = 15
            c_patch = gray[max(0, ch - center_r):min(h, ch + center_r), max(0, cw - center_r):min(w, cw + center_r)]
            rim_patch = gray[max(0, ch - 32):min(h, ch + 32), max(0, cw - 32):min(w, cw + 32)]
            contrast_diff = float(np.mean(rim_patch) - np.mean(c_patch))
            if contrast_diff > 7.0 and not res['is_abadi']:
                pit_detected = True
                res['notes'].append(f"Water/pit dark center contrast (+{contrast_diff:.1f})")

            # -------------------------------------------------------------
            # 4. TUBE WELL / BOREWELL ANALYSIS
            # Compact pump structure / discharge point on field edge / corner
            # -------------------------------------------------------------
            # Tube wells are small compact objects with high contrast in a small 10-20px zone
            c_small = gray[max(0, ch - 12):min(h, ch + 12), max(0, cw - 12):min(w, cw + 12)]
            c_std = float(np.std(c_small))
            surround_std = float(np.std(gray))

            is_compact_pump = (c_std > 20.0 and not pit_detected and not res['is_abadi'] and has_agri_context)
            if is_compact_pump:
                res['is_field_tubewell'] = True
                res['notes'].append("Compact farm pump/borehead pattern in field")

            # -------------------------------------------------------------
            # 5. SYNTHESIZE VALIDITY SCORE & RECOMMENDED TYPE
            # -------------------------------------------------------------
            base_score = res['initial_conf']
            if res['is_abadi']:
                # Disqualify points in residential abadi / built-up structures
                res['validity_score'] = max(0.05, base_score - 0.55)
                res['is_valid'] = False
            elif pit_detected and has_agri_context:
                res['validity_score'] = min(0.98, base_score + 0.35)
                res['recommended_type'] = 'dug'
                res['is_valid'] = True
            elif is_compact_pump and has_agri_context:
                res['validity_score'] = min(0.92, base_score + 0.25)
                res['recommended_type'] = 'tube'
                res['is_valid'] = True
            elif has_agri_context and base_score >= 0.60:
                res['validity_score'] = base_score
                res['is_valid'] = True
            else:
                # Ambiguous or non-agricultural -> reject (NO GUESSING)
                res['validity_score'] = max(0.1, base_score - 0.3)
                res['is_valid'] = False
                res['notes'].append("Ambiguous visual evidence (discarded)")

        except Exception as patch_err:
            logger.warning(f"Error analyzing well patch {well_item.get('id')}: {patch_err}")

        return res

    def reconcile_and_plan_corrections(self, wells, visual_scores, geb_data, excel_hints=None):
        """
        Reconcile detected markings with:
        - Verified visual quality & abadi exclusion
        - GEB Data targets (e.g. GEB Dugwell = 21, GEB Tubewell = 4)
        - Excel column hints (if available)
        
        Strictly enforces:
        1. NO FAKE POINTS: Never invent fake points just to meet GEB counts.
        2. VALIDITY FIRST: Only visually and geographically valid points are kept.
        3. NO GUESSING: Ambiguous / low-confidence detections are pruned.
        4. ACCURATE RECLASSIFICATION: If a genuine field well was marked 'dug' by AI
           but GEB says Dug=0, Tube=53, reclassify valid field points to tube wells!
        """
        target_dug = geb_data.get('geb_dugwell', 0)
        target_tube = geb_data.get('geb_tubewell', 0)
        target_total = geb_data.get('total_geb', 0)

        # Merge with Excel hints if available
        if excel_hints:
            if excel_hints.get('electric_kuva') is not None and target_dug == 0:
                target_dug = int(excel_hints['electric_kuva'])
            if excel_hints.get('electric_bor') is not None and target_tube == 0:
                target_tube = int(excel_hints['electric_bor'])
            if excel_hints.get('total') is not None and target_total == 0:
                target_total = int(excel_hints['total'])

        logger.info(f"GEB Reconcile Targets: Dug={target_dug}, Tube={target_tube}, Total={target_total}")

        # Separate into valid vs invalid candidates
        valid_candidates = []
        to_delete_ids = []

        for v in visual_scores:
            if not v['is_valid'] or v['is_abadi'] or v['validity_score'] < 0.40:
                to_delete_ids.append(v['id'])
            else:
                valid_candidates.append(v)

        # Sort valid candidates by validity score (highest first)
        valid_candidates.sort(key=lambda x: x['validity_score'], reverse=True)

        to_keep = []
        to_adjust = []
        to_reclassify = []

        # Case A: GEB specifies Dug=0, Tube > 0 (e.g. GEB Dug=0, Tube=53)
        if target_dug == 0 and target_tube > 0:
            # All valid field wells should be Tube wells
            for item in valid_candidates:
                if len(to_keep) < target_tube or target_tube == 0:
                    if item['current_type'] != 'tube':
                        to_reclassify.append({
                            'id': item['id'],
                            'new_type': 'tube',
                            'lat': item['lat'],
                            'lon': item['lon']
                        })
                    else:
                        to_keep.append(item['id'])
                        if item['needs_adjust']:
                            to_adjust.append(item)
                else:
                    to_delete_ids.append(item['id'])

        # Case B: Both Dug and Tube targets exist (e.g. Dug=21, Tube=4)
        elif target_dug > 0 or target_tube > 0:
            kept_dug = []
            kept_tube = []

            for item in valid_candidates:
                rec_type = item['recommended_type']

                # Prefer recommended type
                if rec_type == 'dug':
                    if len(kept_dug) < target_dug or target_dug == 0:
                        kept_dug.append(item)
                    elif len(kept_tube) < target_tube:
                        # Reclassify to tube if tube quota has room and agricultural evidence holds
                        item['recommended_type'] = 'tube'
                        kept_tube.append(item)
                        to_reclassify.append({
                            'id': item['id'],
                            'new_type': 'tube',
                            'lat': item['lat'],
                            'lon': item['lon']
                        })
                    else:
                        to_delete_ids.append(item['id'])
                else:  # tube
                    if len(kept_tube) < target_tube or target_tube == 0:
                        kept_tube.append(item)
                    elif len(kept_dug) < target_dug and item['is_circular_dug']:
                        item['recommended_type'] = 'dug'
                        kept_dug.append(item)
                        to_reclassify.append({
                            'id': item['id'],
                            'new_type': 'dug',
                            'lat': item['lat'],
                            'lon': item['lon']
                        })
                    else:
                        to_delete_ids.append(item['id'])

            for item in (kept_dug + kept_tube):
                to_keep.append(item['id'])
                if item['needs_adjust']:
                    to_adjust.append(item)

        # Case C: No GEB data present (keep all genuinely verified points)
        else:
            for item in valid_candidates:
                to_keep.append(item['id'])
                if item['needs_adjust']:
                    to_adjust.append(item)

        plan = {
            'target_geb': {'dug': target_dug, 'tube': target_tube, 'total': target_total},
            'raw_total': len(wells),
            'to_keep_count': len(to_keep),
            'to_delete_ids': to_delete_ids,
            'to_reclassify': to_reclassify,
            'to_adjust': to_adjust,
            'to_keep': to_keep
        }
        return plan

    def execute_corrections(self, session, village_id, csrf, plan, stop_checker=None):
        """
        Execute the Human Review actions on the portal:
        - Delete wrong markings (DELETE /villages/{id}/wells/{well_id})
        - Move / adjust shifted markings (POST /villages/{id}/wells/{well_id}/move)
        - Reclassify types (delete old + add new with correct well_type)
        - Save review & rebuild KML (POST /villages/{id}/finalize)
        """
        results_summary = {
            'deleted_count': 0,
            'reclassified_count': 0,
            'adjusted_count': 0,
            'finalized': False,
            'errors': []
        }

        del_headers = {
            'X-CSRF-TOKEN': csrf,
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        json_headers = {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': csrf,
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }

        # 1. Execute Reclassifications (Delete old well, add new well with correct type)
        for rec in plan.get('to_reclassify', []):
            if stop_checker and stop_checker():
                break
            old_id = rec['id']
            new_type = rec['new_type']
            lat, lon = rec['lat'], rec['lon']
            try:
                # Delete old
                session.delete(f"{self.base_url}/villages/{village_id}/wells/{old_id}", headers=del_headers, timeout=8)
                # Add new
                add_resp = session.post(
                    f"{self.base_url}/villages/{village_id}/wells",
                    headers=json_headers,
                    json={'lat': lat, 'lon': lon, 'well_type': new_type},
                    timeout=8
                )
                if add_resp.status_code in (200, 201):
                    results_summary['reclassified_count'] += 1
            except Exception as e:
                results_summary['errors'].append(f"Reclassify error well {old_id}: {e}")

        # 2. Execute Deletions of false positives / non-well markings concurrently
        delete_ids = plan.get('to_delete_ids', [])
        if delete_ids:
            def _del_one(did):
                if stop_checker and stop_checker():
                    return False
                try:
                    resp = session.delete(
                        f"{self.base_url}/villages/{village_id}/wells/{did}",
                        headers=del_headers,
                        timeout=8
                    )
                    return resp.status_code in (200, 204) or 'deleted' in resp.text
                except Exception as ex:
                    results_summary['errors'].append(f"Delete error well {did}: {ex}")
                    return False

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as del_exec:
                del_futs = [del_exec.submit(_del_one, did) for did in delete_ids]
                for fut in concurrent.futures.as_completed(del_futs):
                    if fut.result():
                        results_summary['deleted_count'] += 1

        # 3. Execute Adjustments / Position fine-tuning
        for adj in plan.get('to_adjust', []):
            if stop_checker and stop_checker():
                break
            well_id = adj['id']
            dx, dy = adj['offset_px']
            # Pixel to lat/lon degrees offset
            # 1 px ≈ 0.3m. lat deg ≈ 111320m. lon deg ≈ 102800m.
            lat_adj = adj['lat'] - (dy * 0.30 / 111320.0)
            lon_adj = adj['lon'] + (dx * 0.30 / 102800.0)
            try:
                mv_resp = session.post(
                    f"{self.base_url}/villages/{village_id}/wells/{well_id}/move",
                    headers=json_headers,
                    json={'lat': lat_adj, 'lon': lon_adj},
                    timeout=8
                )
                if mv_resp.status_code == 200:
                    results_summary['adjusted_count'] += 1
            except Exception as e:
                results_summary['errors'].append(f"Move error well {well_id}: {e}")

        # 4. Save Review & Rebuild KML (Finalize)
        try:
            fin_resp = session.post(
                f"{self.base_url}/villages/{village_id}/finalize",
                data={'_token': csrf},
                timeout=20,
                allow_redirects=False
            )
            if fin_resp.status_code in (200, 301, 302):
                results_summary['finalized'] = True
                logger.info(f"Village {village_id} finalized and KML rebuilt successfully.")
            else:
                results_summary['errors'].append(f"Finalize returned HTTP {fin_resp.status_code}")
        except Exception as e:
            results_summary['errors'].append(f"Finalize exception: {e}")

        return results_summary

    def review_and_correct_village(self, session, review_url, excel_hints=None, stop_checker=None):
        """
        Orchestrate the complete Step 1 - Step 5 Human Review correction workflow for a village:
        - Opens Human Review page
        - Extracts GEB targets and CSRF token
        - Downloads well images and performs Computer Vision & Geospatial analysis
        - Reconciles markings against ground-truth patterns and GEB targets
        - Deletes wrong points, adjusts positions, reclassifies types
        - Finalizes review and rebuilds KML
        - Returns full audit summary and verified review URL
        """
        village_id = self.extract_village_id(review_url)
        if not village_id:
            return {
                'success': False,
                'error': f"Could not extract village ID from {review_url}",
                'review_url': review_url
            }

        t0 = time.time()

        # 1. Parse review page
        review_data, err = self.parse_review_page(session, village_id)
        if err or not review_data:
            return {'success': False, 'error': err, 'review_url': review_url}

        csrf = review_data['csrf']
        geb_data = review_data['geb_data']

        # 2. Fetch Map Data
        map_data, m_err = self.fetch_map_data(session, village_id)
        if m_err or not map_data:
            return {'success': False, 'error': m_err, 'review_url': review_url}

        raw_wells = map_data.get('wells', [])
        initial_counts = map_data.get('counts', {'dug': 0, 'tube': 0, 'total': len(raw_wells)})

        # 3. Analyze each well patch concurrently
        visual_scores = []
        if raw_wells:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as patch_exec:
                futs = [patch_exec.submit(self.analyze_well_patch, session, w) for w in raw_wells]
                for fut in concurrent.futures.as_completed(futs):
                    if stop_checker and stop_checker():
                        break
                    try:
                        visual_scores.append(fut.result())
                    except Exception as p_err:
                        logger.warning(f"Patch evaluation error: {p_err}")

        # 4. Reconcile and build correction plan
        plan = self.reconcile_and_plan_corrections(raw_wells, visual_scores, geb_data, excel_hints)

        # 5. Execute corrections and finalize
        exec_summary = self.execute_corrections(session, village_id, csrf, plan, stop_checker)

        # 6. Verify final map data
        final_map_data, _ = self.fetch_map_data(session, village_id)
        final_counts = (final_map_data or {}).get('counts', {})

        duration = round(time.time() - t0, 2)

        return {
            'success': exec_summary['finalized'],
            'village_id': village_id,
            'review_url': review_url,
            'duration_seconds': duration,
            'initial_counts': initial_counts,
            'final_counts': final_counts,
            'geb_targets': plan['target_geb'],
            'deleted_count': exec_summary['deleted_count'],
            'reclassified_count': exec_summary['reclassified_count'],
            'adjusted_count': exec_summary['adjusted_count'],
            'message': (
                f"Reviewed & Rebuilt: Raw {initial_counts.get('total', len(raw_wells))} -> "
                f"Final {final_counts.get('total', plan['to_keep_count'])} wells "
                f"(Deleted {exec_summary['deleted_count']}, Reclassified {exec_summary['reclassified_count']}, "
                f"Adjusted {exec_summary['adjusted_count']}). "
                f"GEB Target: Dug={plan['target_geb']['dug']}, Tube={plan['target_geb']['tube']}."
            )
        }
