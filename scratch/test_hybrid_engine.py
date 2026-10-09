import requests
import re
import time
import urllib.parse

class DirectPortalClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.csrf_token = None
        self._authenticated = False

    def login(self):
        login_url = f"{self.base_url}/login"
        resp = self.session.get(login_url, timeout=10)
        m = re.search(r'name="_token"\s+value="([^"]+)"', resp.text)
        if not m:
            raise ValueError("CSRF token not found on login page")
        csrf = m.group(1)
        login_resp = self.session.post(login_url, data={
            '_token': csrf,
            'email': self.username,
            'password': self.password,
            'remember': '1'
        }, timeout=10, allow_redirects=True)
        if '/login' in login_resp.url:
            raise ValueError("Login failed: invalid credentials")
        self._authenticated = True
        self._extract_csrf(login_resp.text)
        return True

    def _extract_csrf(self, html):
        meta_m = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        if meta_m:
            self.csrf_token = meta_m.group(1)
        else:
            token_m = re.search(r'name="_token"\s+value="([^"]+)"', html)
            if token_m:
                self.csrf_token = token_m.group(1)

    def process_village(self, village_name, village_code=""):
        v_code = str(village_code or "").strip()
        v_name = str(village_name or "").strip()
        t0 = time.time()

        # Step 1: Search by code first, then by name
        search_term = v_code if v_code else v_name
        search_resp = self.session.get(f"{self.base_url}/?q={urllib.parse.quote_plus(search_term)}", timeout=15)
        self._extract_csrf(search_resp.text)
        html = search_resp.text

        # If not found by code, try by name
        if v_code and ('No villages found' in html or '<tbody' not in html or len(re.findall(r'<tr', html)) <= 1):
            search_resp = self.session.get(f"{self.base_url}/?q={urllib.parse.quote_plus(v_name)}", timeout=15)
            self._extract_csrf(search_resp.text)
            html = search_resp.text

        # Step 2: Check for existing Review link
        # Look specifically in the search result rows
        tbody_m = re.search(r'<tbody[^>]*>(.*?)</tbody>', html, re.DOTALL)
        if not tbody_m:
            return {
                'status': 'FAILED',
                'link': '',
                'message': 'No village records returned by portal search',
                'duration': round(time.time() - t0, 3)
            }

        tbody = tbody_m.group(1)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL)
        if not rows:
            return {
                'status': 'FAILED',
                'link': '',
                'message': 'No village row found in portal search',
                'duration': round(time.time() - t0, 3)
            }

        # Find best matching row
        target_row = rows[0]  # default to first row
        if len(rows) > 1 and v_code:
            for r in rows:
                if v_code in r:
                    target_row = r
                    break

        # Check if already reviewed
        rev_m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', target_row)
        if rev_m:
            rev_url = rev_m.group(1)
            return {
                'status': 'SUCCESS',
                'link': rev_url,
                'message': 'Generated successfully (reviewed)',
                'duration': round(time.time() - t0, 3)
            }

        # Check if "No boundary"
        if 'No boundary' in target_row:
            return {
                'status': 'FAILED',
                'link': '',
                'message': 'No boundary geometry found on portal',
                'duration': round(time.time() - t0, 3)
            }

        # Check if already processing / has village record ID
        village_rec_m = re.search(r'action="https://generate\.snsies\.com/villages/(\d+)"', target_row)
        if village_rec_m and 'badge processing' in target_row:
            v_rec_id = village_rec_m.group(1)
            candidate_url = f"{self.base_url}/villages/{v_rec_id}/review"
            chk = self.session.get(candidate_url, timeout=10)
            if chk.status_code == 200:
                return {
                    'status': 'SUCCESS',
                    'link': candidate_url,
                    'message': 'Generated successfully (completed)',
                    'duration': round(time.time() - t0, 3)
                }

        # Check if pending generation (has button or data-village-id)
        btn_m = re.search(r'data-village-id="(\d+)"', target_row)
        if btn_m:
            village_word_id = btn_m.group(1)
            # Submit generation POST
            payload = {
                '_token': self.csrf_token or '',
                'imagery_provider': 'google',
                'use_ai': '0'
            }
            gen_resp = self.session.post(
                f"{self.base_url}/village-words/{village_word_id}/detect",
                data=payload,
                timeout=90,
                allow_redirects=False
            )
            # Check 302 redirect
            if gen_resp.status_code in (301, 302):
                loc = gen_resp.headers.get('Location')
                if loc and '/review' in loc:
                    # Verify 200
                    v_chk = self.session.get(loc, timeout=10)
                    if v_chk.status_code == 200:
                        return {
                            'status': 'SUCCESS',
                            'link': loc,
                            'message': 'Generated successfully (live detection)',
                            'duration': round(time.time() - t0, 3)
                        }

            # If not direct redirect, poll search for up to 60s
            poll_start = time.time()
            while time.time() - poll_start < 60:
                time.sleep(2)
                p_resp = self.session.get(f"{self.base_url}/?q={urllib.parse.quote_plus(search_term)}", timeout=10)
                p_m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', p_resp.text)
                if p_m:
                    return {
                        'status': 'SUCCESS',
                        'link': p_m.group(1),
                        'message': 'Generated successfully (polled completion)',
                        'duration': round(time.time() - t0, 3)
                    }

        return {
            'status': 'FAILED',
            'link': '',
            'message': 'Generation could not be triggered or timed out',
            'duration': round(time.time() - t0, 3)
        }

if __name__ == '__main__':
    client = DirectPortalClient("https://generate.snsies.com/", "admin@kmltodata.local", "Admin@12345")
    client.login()
    print("Client logged in successfully.")

    test_villages = [
        ("Bharkunda", "511639"),
        ("Abhepar", "512317"),
        ("Timbla", "511863"),
        ("Panar", "511494"),
        ("Changodar (Og)", "511624"),
        ("(2) Rampura", "511130"),  # Known "No boundary"
    ]

    for name, code in test_villages:
        res = client.process_village(name, code)
        print(f"[{code}] {name} -> {res['status']} in {res['duration']}s: {res['link'] or res['message']}")
