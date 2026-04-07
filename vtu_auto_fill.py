from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime
import pytz
import time, json, os, sys


# ── LOAD CREDENTIALS FROM ENV ─────────────────────────────
USERNAME = os.environ.get("VTU_USERNAME")
PASSWORD = os.environ.get("VTU_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing GitHub secrets")
    sys.exit(1)


# ── LOAD TODAY'S ENTRY USING IST TIMEZONE ─────────────────
ist = pytz.timezone("Asia/Kolkata")
today_str = datetime.now(ist).date().isoformat()

with open("entries.json", "r") as f:
    all_entries = json.load(f)

if today_str not in all_entries:
    print(f"ℹ️ No entry scheduled for {today_str}")
    sys.exit(0)

entry = all_entries[today_str]

SUMMARY  = entry["summary"]
LEARNING = entry["learning"]
BLOCKERS = entry.get("blockers", "No blockers today")
LINKS    = entry.get("links", "")
HOURS    = entry.get("hours", "6")
SKILLS   = entry.get("skills", ["Python", "Machine Learning"])

print(f"📅 Running entry for {today_str}")


# ── CHROME OPTIONS FOR GITHUB ACTIONS ─────────────────────
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)


# ── LOGIN ────────────────────────────────────────────────
driver.get("https://vtu.internyet.in/sign-in")

wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "input[placeholder='Enter your email address']")
    )
).send_keys(USERNAME)

driver.find_element(By.ID, "password").send_keys(PASSWORD)

driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

wait.until(lambda d: "dashboard" in d.current_url.lower())

print("✅ Login successful")


# ── HANDLE OPTIONAL MODAL ─────────────────────────────────
try:
    modal_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Understand')]")
        )
    )
    modal_btn.click()
    print("✅ Modal dismissed")

except:
    pass


# ── NAVIGATE TO DIARY PAGE ───────────────────────────────
wait.until(
    EC.element_to_be_clickable(
        (By.LINK_TEXT, "Internship Diary")
    )
).click()

print("✅ Navigated to Internship Diary")


# ── SELECT INTERNSHIP ────────────────────────────────────
wait.until(
    EC.element_to_be_clickable((By.ID, "internship_id"))
).click()

wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//div[@role='option']")
    )
).click()

print("✅ Selected internship")


# ── SELECT TODAY DATE ────────────────────────────────────
wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@aria-label,'Today')]")
    )
).click()

print("✅ Selected today's date")


# ── CONTINUE ─────────────────────────────────────────────
wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Continue')]")
    )
).click()

print("✅ Continue clicked")


# ── DUPLICATE ENTRY GUARD ────────────────────────────────
wait.until(
    lambda d:
    "already submitted" in d.page_source.lower()
    or "briefly describe the work you did today" in d.page_source.lower()
)

if "already submitted" in driver.page_source.lower():

    print("⚠️ Entry already exists")

    driver.quit()
    sys.exit(0)


# ── WAIT FOR FORM ─────────────────────────────────────────
wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//textarea[contains(@placeholder,'Briefly describe')]")
    )
)

print("✅ Diary form loaded")


# ── FILL SUMMARY ─────────────────────────────────────────
driver.find_element(
    By.XPATH,
    "//textarea[contains(@placeholder,'Briefly describe')]"
).send_keys(SUMMARY)


# ── HOURS ────────────────────────────────────────────────
driver.find_element(
    By.XPATH,
    "//input[@placeholder='e.g. 6.5']"
).send_keys(HOURS)


# ── LINKS ────────────────────────────────────────────────
if LINKS:

    driver.find_element(
        By.XPATH,
        "//textarea[contains(@placeholder,'relevant links')]"
    ).send_keys(LINKS)


# ── LEARNINGS ────────────────────────────────────────────
driver.find_element(
    By.XPATH,
    "//textarea[contains(@placeholder,'learn or ship')]"
).send_keys(LEARNING)


# ── BLOCKERS ─────────────────────────────────────────────
driver.find_element(
    By.XPATH,
    "//textarea[contains(@placeholder,'slowed you down')]"
).send_keys(BLOCKERS)


# ── SKILLS ───────────────────────────────────────────────
for skill in SKILLS:

    skills_input = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//input[contains(@id,'react-select')]")
        )
    )

    skills_input.send_keys(skill)
    time.sleep(1)
    skills_input.send_keys(Keys.RETURN)


print("✅ Skills added")


# ── SAVE ENTRY ───────────────────────────────────────────
wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Save')]")
    )
).click()


# ── VERIFY SERVER ACCEPTED SUBMISSION ─────────────────────
wait.until(
    lambda d:
    "entries" in d.current_url.lower()
    or "submitted" in d.page_source.lower()
)

print(" Diary entry successfully submitted")


driver.quit()