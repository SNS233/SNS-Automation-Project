import os
import time
import json
import logging
import urllib.parse
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException,
    UnexpectedAlertPresentException,
    NoAlertPresentException
)

from config import Config

logger = logging.getLogger(__name__)

class PortalBrowserAutomator:
    """
    Real browser automation driver for the Village Well Detector portal.
    Executes actual user actions:
    1. Opens portal in real Chrome browser
    2. Authenticates if login is required (reusing session)
    3. Searches and selects the correct village using Village Code & Name
    4. Triggers the existing Generate action or detects already reviewed link
    5. Dynamically waits for generation completion (event-based, no fixed sleeps)
    6. Captures the EXACT final URL reached by the browser
    7. Diagnostic capture (screenshots, JSON logs, console errors) on failure
    8. Safe recovery checks before any failure is declared
    Never fabricates, normalizes, or hardcodes any URL pattern.
    """

    def __init__(self, portal_url=None, username=None, password=None, headless=True):
        self.portal_url = (portal_url or Config.PORTAL_URL or Config.MARKING_PORTAL_URL or "https://generate.snsies.com/").rstrip('/')
        self.username = username or Config.PORTAL_USERNAME or Config.MARKING_PORTAL_USER or ""
        self.password = password or Config.PORTAL_PASSWORD or Config.MARKING_PORTAL_PASSWORD or ""
        self.headless = headless if headless is not None else Config.PORTAL_HEADLESS
        self.driver = None
        self.is_logged_in = False
        
        # Diagnostics directory
        self.diag_dir = Config.AUTOMATION_UPLOAD_DIR / "diagnostics"
        self.diag_dir.mkdir(parents=True, exist_ok=True)

    def _get_chromedriver_path(self):
        """Locate existing chromedriver executable on the system."""
        known_paths = [
            r"C:\Users\Admin\.cache\selenium\chromedriver\win64\154.0.8037.92\chromedriver.exe",
        ]
        cache_base = Path(os.path.expanduser(r"~\.cache\selenium\chromedriver"))
        if cache_base.exists():
            for p in cache_base.glob("**/chromedriver.exe"):
                if p.is_file():
                    known_paths.insert(0, str(p))

        for path_str in known_paths:
            if os.path.exists(path_str):
                return path_str
        return None

    def start(self):
        """Initialize the real Chrome browser instance."""
        if self.driver:
            return self.driver

        chrome_binary = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        driver_path = self._get_chromedriver_path()

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if os.path.exists(chrome_binary):
            options.binary_location = chrome_binary

        if driver_path and os.path.exists(driver_path):
            service = Service(executable_path=driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.set_page_load_timeout(60)
        self.driver.implicitly_wait(3)
        logger.info(f"Started Chrome browser session (headless={self.headless}).")
        return self.driver

    def close(self):
        """Cleanly close the browser session."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.debug(f"Notice while closing browser: {e}")
            finally:
                self.driver = None
                self.is_logged_in = False
                logger.info("Closed Chrome browser session.")

    def dismiss_unexpected_alert(self):
        """Dismiss or accept any unexpected JavaScript alert so browser does not freeze."""
        if not self.driver:
            return None
        try:
            alert = self.driver.switch_to.alert
            text = alert.text
            logger.warning(f"Unexpected browser alert detected: '{text}'. Accepting to continue.")
            alert.accept()
            return text
        except (NoAlertPresentException, Exception):
            return None

    def ensure_authenticated(self):
        """
        Navigate to portal and log in if login page is displayed.
        Reuses active session across villages.
        """
        if self.is_logged_in:
            return True, "Already authenticated"

        # Attempt to connect to portal with retry for intermittent network
        for attempt in range(3):
            try:
                self.start()
                logger.info(f"Navigating to portal URL: {self.portal_url} (attempt {attempt+1}/3)")
                self.driver.get(self.portal_url)
                break
            except WebDriverException as e:
                if attempt < 2:
                    logger.warning(f"Connection glitch accessing portal (attempt {attempt+1}): {e}. Retrying in 2s...")
                    time.sleep(2)
                else:
                    return False, f"Could not connect to portal after 3 attempts: {e}"

        self.dismiss_unexpected_alert()
        curr_url = self.driver.current_url.lower()

        # Check if portal requires login
        is_login_page = (
            "/login" in curr_url or
            "login" in self.driver.title.lower() or
            len(self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")) > 0
        )

        if not is_login_page:
            self.is_logged_in = True
            logger.info("Portal does not require login or is already authenticated.")
            return True, "No login required"

        # Login is required
        logger.info("Portal login page detected. Attempting authentication...")
        if not self.username or not self.password:
            msg = "Portal requires login, but PORTAL_USERNAME and PORTAL_PASSWORD are not configured."
            logger.warning(msg)
            return False, msg

        try:
            # Find email/username field
            email_field = None
            email_selectors = [
                "input[name='email']",
                "input[type='email']",
                "input[name='username']",
                "input[id='email']",
                "input[id='username']",
                "input[type='text']"
            ]
            for sel in email_selectors:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if elems and elems[0].is_displayed():
                    email_field = elems[0]
                    break

            if not email_field:
                return False, "Could not find username/email input field on login page."

            email_field.clear()
            email_field.send_keys(self.username)

            # Find password field
            pwd_field = None
            pwd_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[id='password']"
            ]
            for sel in pwd_selectors:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if elems and elems[0].is_displayed():
                    pwd_field = elems[0]
                    break

            if not pwd_field:
                return False, "Could not find password input field on login page."

            pwd_field.clear()
            pwd_field.send_keys(self.password)

            # Check remember checkbox if present
            remember_boxes = self.driver.find_elements(By.CSS_SELECTOR, "input[name='remember'], input[type='checkbox']")
            if remember_boxes and not remember_boxes[0].is_selected():
                try:
                    remember_boxes[0].click()
                except Exception:
                    pass

            # Submit login form
            submit_btn = None
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button.btn-primary",
                "button.btn"
            ]
            for sel in submit_selectors:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if elems and elems[0].is_displayed():
                    submit_btn = elems[0]
                    break

            if submit_btn:
                submit_btn.click()
            else:
                pwd_field.send_keys(Keys.ENTER)

            # Wait for redirect away from /login
            WebDriverWait(self.driver, 15).until(
                lambda d: "/login" not in d.current_url.lower()
            )

            self.is_logged_in = True
            logger.info("Successfully authenticated on external portal.")
            return True, "Login successful"

        except TimeoutException:
            err_text = ""
            for err_sel in [".alert-danger", ".invalid-feedback", ".text-danger", ".error"]:
                err_elems = self.driver.find_elements(By.CSS_SELECTOR, err_sel)
                if err_elems and err_elems[0].text.strip():
                    err_text = err_elems[0].text.strip()
                    break

            msg = f"Login failed on {self.portal_url}: {err_text or 'Invalid credentials or login timeout.'}"
            logger.warning(msg)
            return False, msg
        except Exception as e:
            msg = f"Error during login: {str(e)}"
            logger.error(msg)
            return False, msg

    def search_and_select_village(self, village_name, village_code=None):
        """
        Locate the exact village row using Village Code as primary unique key,
        falling back to Village Name.
        """
        self.start()
        self.dismiss_unexpected_alert()
        v_name = (village_name or "").strip()
        v_code = str(village_code or "").strip()
        if v_code.lower() in ('nan', 'none', '0'):
            v_code = ""

        search_terms = []
        if v_code:
            search_terms.append(v_code)
        if v_name and v_name not in search_terms:
            search_terms.append(v_name)

        matching_elem = None

        for term in search_terms:
            if not term:
                continue
            quoted = urllib.parse.quote_plus(term)
            target_url = f"{self.portal_url}/?q={quoted}"
            
            try:
                self.driver.get(target_url)
                # Wait for table to be present
                WebDriverWait(self.driver, 4).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody"))
                )
            except Exception:
                pass

            self.dismiss_unexpected_alert()
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for row in rows:
                text = row.text.strip().lower()
                # Exact code match check: e.g. (511489)
                if v_code and f"({v_code.lower()})" in text:
                    matching_elem = row
                    break
                elif v_code and v_code.lower() in text:
                    matching_elem = row
                    break
                elif v_name and v_name.lower() in text:
                    matching_elem = row
                    break

            if matching_elem:
                break

        return matching_elem

    def trigger_generate_action(self, matching_elem=None, village_name="", village_code=""):
        """
        Execute the portal's action for this village:
        - Case 1: If the village already has an active Review link, open it directly.
        - Case 2: If the village is pending, click Generate in the row, wait for the
          detect modal (#detect-modal), and click #detect-modal-submit.
        Never clicks unrelated buttons at the top of the page.
        """
        initial_handles = set(self.driver.window_handles)
        initial_url = self.driver.current_url
        self.dismiss_unexpected_alert()

        # Case 1: Check if matching row already has a Review link
        if matching_elem:
            review_links = matching_elem.find_elements(By.CSS_SELECTOR, "a[href*='/review']")
            if review_links:
                href = review_links[0].get_attribute("href")
                logger.info(f"Village already has Review link in row ({href}). Accessing directly.")
                try:
                    review_links[0].click()
                except Exception:
                    self.driver.get(href)
                return initial_handles, initial_url

        # Case 2: Find Generate/Update button strictly INSIDE the matching village row
        row_btn = None
        if matching_elem:
            btns = matching_elem.find_elements(
                By.CSS_SELECTOR,
                "button.js-open-detect, button[data-mode='generate'], button[data-mode='update'], button.btn"
            )
            for b in btns:
                if b.is_displayed():
                    row_btn = b
                    break

        if not row_btn:
            raise NoSuchElementException(
                f"Could not find Generate action button inside the village row for '{village_name}' (Code: {village_code})."
            )

        # Click the row's Generate button
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row_btn)
            row_btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", row_btn)

        self.dismiss_unexpected_alert()

        # Check if detect modal opened (#detect-modal)
        try:
            modal_submit = WebDriverWait(self.driver, 2.5).until(
                EC.element_to_be_clickable((By.ID, "detect-modal-submit"))
            )
            logger.info("Detection modal opened. Submitting detection form...")
            try:
                modal_submit.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", modal_submit)
        except TimeoutException:
            logger.debug("Modal submit button did not appear; checking if navigation already started.")

        return initial_handles, initial_url

    def wait_and_capture_final_url(self, initial_handles, initial_url, max_wait_seconds=360, poll_interval=0.25, stop_checker=None, village_name="", village_code=""):
        """
        Wait for existing generation process to finish and capture the REAL URL reached.
        Uses fast event-driven polling (0.25s) to capture URL immediately upon completion.
        Includes safe re-check recovery before timing out.
        """
        start_time = time.time()
        logger.info(f"Observing browser navigation for '{village_name}' (poll: {poll_interval}s)...")

        while (time.time() - start_time) < max_wait_seconds:
            if stop_checker and stop_checker():
                raise InterruptedError("Automation was stopped by user.")

            self.dismiss_unexpected_alert()

            # Case 1: Portal opened a new tab / window
            current_handles = set(self.driver.window_handles)
            new_handles = current_handles - initial_handles
            if new_handles:
                new_tab = list(new_handles)[0]
                self.driver.switch_to.window(new_tab)
                if self._is_navigation_settled():
                    final_url = self.driver.current_url
                    logger.info(f"Captured real final URL from new tab: {final_url}")
                    try:
                        self.driver.close()
                    except Exception:
                        pass
                    if initial_handles:
                        self.driver.switch_to.window(list(initial_handles)[0])
                    return final_url

            # Case 2: Current tab navigated to review / village result page
            curr_url = self.driver.current_url
            if "/review" in curr_url.lower() or ("/villages/" in curr_url.lower() and "/download" not in curr_url.lower()):
                if self._is_navigation_settled():
                    logger.info(f"Captured real final URL from redirect: {curr_url}")
                    return curr_url

            # Case 3: URL changed from initial and settled
            if curr_url != initial_url:
                if self._is_navigation_settled():
                    logger.info(f"Captured real final URL from navigation: {curr_url}")
                    return curr_url

            # Case 4: On same page, check if result markers loaded
            if self._is_result_page_ready():
                logger.info(f"Captured real final URL from page result: {curr_url}")
                return curr_url

            time.sleep(poll_interval)

        # -------------------------------------------------------------
        # Safe Recovery Check (Requirement 7):
        # Re-check the portal table to see if generation actually completed
        # in the background and a Review link is now available!
        # -------------------------------------------------------------
        logger.info(f"Generation timeout elapsed for '{village_name}'. Performing recovery check on portal...")
        recovered_url = self.recover_and_check_result(village_name, village_code)
        if recovered_url:
            logger.info(f"RECOVERY SUCCESS: Captured newly generated Review URL for '{village_name}': {recovered_url}")
            return recovered_url

        # Genuinely timed out: Capture full diagnostics & screenshots
        self.capture_diagnostics(village_name, village_code, "03_timeout_error", error_msg="Generation timed out")
        raise TimeoutError(f"Generation timed out after {max_wait_seconds} seconds without final page completion.")

    def recover_and_check_result(self, village_name, village_code):
        """
        Check if the village row now displays a completed Review link.
        Guarantees that background generations are not falsely marked FAILED.
        """
        try:
            term = village_code or village_name
            if not term:
                return None
            quoted = urllib.parse.quote_plus(term)
            self.driver.get(f"{self.portal_url}/?q={quoted}")
            time.sleep(1.0)
            self.dismiss_unexpected_alert()

            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for row in rows:
                text = row.text.strip().lower()
                code_match = (village_code and village_code.lower() in text)
                name_match = (village_name and village_name.lower() in text)
                if code_match or name_match:
                    review_links = row.find_elements(By.CSS_SELECTOR, "a[href*='/review']")
                    if review_links:
                        href = review_links[0].get_attribute("href")
                        if href and href.startswith("http"):
                            return href
            return None
        except Exception as e:
            logger.debug(f"Recovery check notice: {e}")
            return None

    def capture_diagnostics(self, village_name, village_code, step_name, error_msg=None):
        """
        Save diagnostic screenshots, DOM details, and console logs.
        Sanitizes sensitive information (never logs passwords).
        """
        if not self.driver:
            return
        try:
            timestamp = int(time.time())
            clean_code = str(village_code or "nocode").strip()
            clean_step = str(step_name).replace(" ", "_")

            # 1. Screenshot
            screenshot_path = self.diag_dir / f"{timestamp}_{clean_code}_{clean_step}.png"
            self.driver.save_screenshot(str(screenshot_path))

            # 2. Console logs
            console_logs = []
            try:
                for entry in self.driver.get_log('browser'):
                    # Omit passwords
                    msg = entry.get('message', '')
                    if self.password and self.password in msg:
                        msg = msg.replace(self.password, '***')
                    console_logs.append({
                        "level": entry.get('level'),
                        "message": msg[:300]
                    })
            except Exception:
                pass

            # 3. Diagnostic JSON report
            body_text = ""
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text[:800]
            except Exception:
                pass

            diag_data = {
                "timestamp": timestamp,
                "village_name": village_name,
                "village_code": clean_code,
                "step": step_name,
                "current_url": self.driver.current_url,
                "page_title": self.driver.title,
                "page_text_snippet": body_text,
                "window_handles_count": len(self.driver.window_handles),
                "error_message": error_msg or "",
                "screenshot": screenshot_path.name,
                "console_errors": console_logs
            }

            json_path = self.diag_dir / f"{timestamp}_{clean_code}_{clean_step}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(diag_data, f, indent=2)

        except Exception as diag_err:
            logger.debug(f"Notice while capturing diagnostics: {diag_err}")

    def _is_navigation_settled(self):
        """Check if browser document readyState is complete and processing overlay has finished."""
        try:
            ready = self.driver.execute_script("return document.readyState")
            if ready != "complete":
                return False

            # Check if processing overlay is active
            overlays = self.driver.find_elements(By.CSS_SELECTOR, "#processing-overlay.open, .processing-overlay.open")
            if overlays and overlays[0].is_displayed():
                return False

            body_elem = self.driver.find_element(By.TAG_NAME, "body")
            body_classes = body_elem.get_attribute("class") or ""
            if "is-processing" in body_classes:
                return False

            body_text = body_elem.text.lower()
            generating_indicators = [
                "generating...",
                "processing generation",
                "in progress, please wait",
                "detecting wells..."
            ]
            for ind in generating_indicators:
                if ind in body_text:
                    return False

            spinners = self.driver.find_elements(By.CSS_SELECTOR, ".spinner-border, .loading-spinner, .fa-spin")
            for sp in spinners:
                if sp.is_displayed():
                    return False

            return True
        except Exception:
            return False

    def _is_result_page_ready(self):
        """Check if portal has displayed generated review or result content on the page."""
        try:
            curr_url = self.driver.current_url.lower()
            if "/review" in curr_url or ("/villages/" in curr_url and "/download" not in curr_url):
                return True

            result_indicators = [
                ".review-table",
                "#resultTable",
                ".wells-list",
                ".kml-result",
                "table[data-result='true']"
            ]
            for sel in result_indicators:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if elems and elems[0].is_displayed():
                    return True
            return False
        except Exception:
            return False
