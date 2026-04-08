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


# ── CREDENTIALS ───────────────────────────────────────────
USERNAME = os.environ.get("VTU_USERNAME")
PASSWORD = os.environ.get("VTU_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing GitHub secrets")
    sys.exit(1)


# ── LOAD TODAY'S ENTRY ────────────────────────────────────
ist = pytz.timezone("Asia/Kolkata")
today_str = datetime.now(ist).date().isoformat()

with open("entries.json", "r") as f:
    all_entries = json.load(f)

if today_str not in all_entries:
    print(f"ℹ️ No entry scheduled for {today_str}")
    sys.exit(0)

entry    = all_entries[today_str]
SUMMARY  = entry["summary"]
LEARNING = entry["learning"]
BLOCKERS = entry.get("blockers", "No blockers today")
LINKS    = entry.get("links", "")
HOURS    = str(entry.get("hours", "6"))
SKILLS   = entry.get("skills", ["Python", "Machine Learning"])

print(f"📅 Running entry for {today_str}")


# ── CHROME OPTIONS (GITHUB ACTIONS HEADLESS) ──────────────
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 40)


# ── LOGIN ─────────────────────────────────────────────────
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


# ── HANDLE MODAL ──────────────────────────────────────────
try:
    modal_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Understand')]")
    ))
    driver.execute_script("arguments[0].click();", modal_btn)
    print("✅ Modal dismissed")
    time.sleep(1)
except:
    print("ℹ️ No modal")

try:
    wait.until(EC.invisibility_of_element_located(
        (By.CSS_SELECTOR, "div[class*='bg-black']")
    ))
except:
    pass


# ── NAVIGATE TO DIARY ─────────────────────────────────────
diary_link = wait.until(
    EC.presence_of_element_located((By.LINK_TEXT, "Internship Diary"))
)
driver.execute_script("arguments[0].click();", diary_link)
print("✅ Navigated to Internship Diary")
time.sleep(2)


# ── SELECT INTERNSHIP ─────────────────────────────────────
internship_btn = wait.until(
    EC.element_to_be_clickable((By.ID, "internship_id"))
)
driver.execute_script("arguments[0].click();", internship_btn)
time.sleep(1)

mit_option = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//div[@role='option' and contains(.,'Research Internship at MIT')]")
    )
)
driver.execute_script("arguments[0].click();", mit_option)
print("✅ Selected internship")
time.sleep(1)


# ── SELECT DATE (IST) ─────────────────────────────────────
date_trigger = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[@aria-haspopup='dialog']")
    )
)
driver.execute_script("arguments[0].click();", date_trigger)
print("✅ Date picker opened")
time.sleep(1)

now_ist     = datetime.now(ist)
today_day   = str(now_ist.day)
today_month = now_ist.strftime("%B")
today_year  = str(now_ist.year)
print(f"📅 IST today: {today_day} {today_month} {today_year}")

today_btn = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH,
         f"//button[contains(@aria-label,'{today_month}') and "
         f"contains(@aria-label,'{today_year}') and "
         f"not(contains(@aria-label,'Go to')) and "
         f"normalize-space(text())='{today_day}']"
        )
    )
)
label = today_btn.get_attribute("aria-label")
print(f"📅 Clicking: {label}")
driver.execute_script("arguments[0].click();", today_btn)
print(f"✅ Date selected: {label}")
time.sleep(0.5)


# ── CONTINUE ──────────────────────────────────────────────
continue_btn = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Continue')]")
    )
)
driver.execute_script("arguments[0].click();", continue_btn)
print("✅ Continue clicked")


# ── DUPLICATE GUARD ───────────────────────────────────────
wait.until(
    lambda d:
    "already submitted" in d.page_source.lower()
    or "briefly describe the work you did today" in d.page_source.lower()
)

if "already submitted" in driver.page_source.lower():
    print("⚠️ Entry already exists for today. Skipping.")
    driver.quit()
    sys.exit(0)


# ── WAIT FOR FORM ─────────────────────────────────────────
wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//textarea[contains(@placeholder,'Briefly describe')]")
    )
)
print("✅ Diary form loaded")


# ── FILL SUMMARY ──────────────────────────────────────────
driver.find_element(
    By.XPATH, "//textarea[contains(@placeholder,'Briefly describe')]"
).send_keys(SUMMARY)


# ── HOURS ─────────────────────────────────────────────────
driver.find_element(
    By.XPATH, "//input[@placeholder='e.g. 6.5']"
).send_keys(HOURS)


# ── LINKS ─────────────────────────────────────────────────
if LINKS:
    driver.find_element(
        By.XPATH, "//textarea[contains(@placeholder,'relevant links')]"
    ).send_keys(LINKS)


# ── LEARNINGS ─────────────────────────────────────────────
driver.find_element(
    By.XPATH, "//textarea[contains(@placeholder,'learn or ship')]"
).send_keys(LEARNING)


# ── BLOCKERS ──────────────────────────────────────────────
driver.find_element(
    By.XPATH, "//textarea[contains(@placeholder,'slowed you down')]"
).send_keys(BLOCKERS)


# ── SKILLS ────────────────────────────────────────────────
for skill in SKILLS:
    skills_input = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//input[contains(@id,'react-select')]")
        )
    )
    skills_input.click()
    skills_input.send_keys(skill)
    time.sleep(1)
    skills_input.send_keys(Keys.RETURN)
    time.sleep(0.8)

print("✅ Skills added")


# ── CLOSE SKILLS DROPDOWN BEFORE SAVING ───────────────────
webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
time.sleep(0.5)
driver.find_element(By.TAG_NAME, "body").click()
time.sleep(0.5)


# ── SAVE ──────────────────────────────────────────────────
save_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Save')]")
    )
)
driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
time.sleep(0.5)
driver.execute_script("arguments[0].click();", save_button)
print("✅ Save clicked")


# ── VERIFY ────────────────────────────────────────────────
try:
    wait.until(
        lambda d:
        "edit-diary-entry" in d.current_url.lower()
        or "diary-entries" in d.current_url.lower()
    )
    print("✅ Diary entry successfully submitted!")
    print(f"📍 Final URL: {driver.current_url}")
except:
    driver.save_screenshot("save_failed.png")
    print("⚠️ Save failed — screenshot saved")
    print(f"📍 Current URL: {driver.current_url}")
    sys.exit(1)


driver.quit()