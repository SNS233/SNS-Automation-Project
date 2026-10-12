import sys
import io
import time
from selenium.webdriver.common.by import By

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from services.browser_automation import PortalBrowserAutomator

automator = PortalBrowserAutomator(
    portal_url="https://generate.snsies.com/",
    username="admin@kmltodata.local",
    password="Admin@12345",
    headless=True
)

try:
    automator.start()
    automator.ensure_authenticated()
    driver = automator.driver

    # Let's test Timbla (511863) - pending village
    v_name = "Timbla"
    v_code = "511863"
    print(f"\n--- TIMING BREAKDOWN FOR PENDING VILLAGE: {v_name} ({v_code}) ---")
    t0 = time.time()

    # Step 1: Search
    t_search_start = time.time()
    driver.get(f"https://generate.snsies.com/?q={v_code}")
    t_search_end = time.time()
    print(f"1. Search navigation took: {t_search_end - t_search_start:.3f}s")

    # Step 2: Locate row
    t_row_start = time.time()
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"2. Found {len(rows)} rows in: {time.time() - t_row_start:.3f}s")
    assert rows, "Must find row"
    row = rows[0]
    print(f"   Row text: {row.text.split(chr(10))[0]}")

    # Step 3: Trigger
    t_trig_start = time.time()
    gen_btn = row.find_element(By.CSS_SELECTOR, "button.js-open-detect")
    gen_btn.click()
    print(f"3. Click row button took: {time.time() - t_trig_start:.3f}s")

    # Step 4: Modal submit
    t_modal_start = time.time()
    submit_btn = driver.find_element(By.ID, "detect-modal-submit")
    submit_btn.click()
    print(f"4. Modal submit took: {time.time() - t_modal_start:.3f}s")

    # Step 5: Wait for final URL
    t_wait_start = time.time()
    while time.time() - t_wait_start < 60:
        curr_url = driver.current_url
        if "/review" in curr_url or ("/villages/" in curr_url and "/download" not in curr_url):
            break
        time.sleep(0.2)
    t_wait_end = time.time()
    print(f"5. Navigation to review URL took: {t_wait_end - t_wait_start:.3f}s")
    print(f"   Final URL: {driver.current_url}")

    total_time = time.time() - t0
    print(f"TOTAL TIME FOR PENDING VILLAGE: {total_time:.3f}s")

finally:
    automator.close()
