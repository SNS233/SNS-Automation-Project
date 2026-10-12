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

    print("\n--- INSPECTING BULK GENERATE PAGE ---")
    driver.get("https://generate.snsies.com/bulk")
    time.sleep(2)
    print("URL:", driver.current_url)
    print("Title:", driver.title)
    print("Page text snippet:\n", driver.find_element(By.TAG_NAME, "body").text[:1500])

    forms = driver.find_elements(By.TAG_NAME, "form")
    for f in forms:
        print("\nForm:", f.get_attribute("action"), f.get_attribute("method"))
        for inp in f.find_elements(By.TAG_NAME, "input"):
            print("  Inp:", inp.get_attribute("name"), inp.get_attribute("type"))

finally:
    automator.close()
