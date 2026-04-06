from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import date
import time, json, os, sys



# ── LOAD CREDENTIALS FROM ENV ─────────────────────────────────────────────────
USERNAME = os.environ.get("VTU_USERNAME")
PASSWORD = os.environ.get("VTU_PASSWORD")

# ── LOAD TODAY'S ENTRY FROM JSON ──────────────────────────────────────────────
today_str = date.today().isoformat()  # e.g. "2026-04-07"

with open("entries.json", "r") as f:
    all_entries = json.load(f)

if today_str not in all_entries:
    print(f"ℹ️ No entry scheduled for {today_str}. Exiting.")
    sys.exit(0)

entry = all_entries[today_str]
SUMMARY  = entry["summary"]
LEARNING = entry["learning"]
BLOCKERS = entry.get("blockers", "No major blockers today.")
LINKS    = entry.get("links", "")
HOURS    = entry.get("hours", "6")
SKILLS   = entry.get("skills", ["Python", "Machine Learning"])

print(f"📅 Running entry for {today_str}")

# ── CHROME OPTIONS ────────────────────────────────────────────────────────────
options = webdriver.ChromeOptions()
options.add_argument("--headless")               # required for GitHub Actions
options.add_argument("--no-sandbox")             # required for GitHub Actions
options.add_argument("--disable-dev-shm-usage")  # required for GitHub Actions
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 30)

# ── LOGIN ─────────────────────────────────────────────────────────────────────
driver.get("https://vtu.internyet.in/sign-in")
email_input = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter your email address']"))
)
email_input.send_keys(USERNAME)
driver.find_element(By.CSS_SELECTOR, "input[id='password']").send_keys(PASSWORD)
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
wait.until(lambda d: "dashboard" in d.current_url.lower())
print("✅ Login successful")

# ── DISMISS MODAL ─────────────────────────────────────────────────────────────
try:
    btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'I Understand') or contains(text(),'I understand')]")
    ))
    driver.execute_script("arguments[0].click();", btn)
    print("✅ Modal dismissed")
except:
    print("ℹ️ No modal found")

try:
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[class*='bg-black']")))
except:
    pass
time.sleep(1)

# ── NAVIGATE TO INTERNSHIP DIARY ──────────────────────────────────────────────
diary_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Internship Diary")))
driver.execute_script("arguments[0].click();", diary_link)
print("✅ Navigated to Internship Diary")
time.sleep(2)

# ── SELECT INTERNSHIP ─────────────────────────────────────────────────────────
internship_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#internship_id")))
driver.execute_script("arguments[0].click();", internship_btn)
time.sleep(1)
mit_option = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[@role='option' and contains(., 'Research Internship at MIT')]")
))
driver.execute_script("arguments[0].click();", mit_option)
print("✅ Selected internship")
time.sleep(1)

# ── OPEN DATE PICKER ──────────────────────────────────────────────────────────
date_btn = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//button[@aria-haspopup='dialog' and .//span[contains(text(),'Pick a Date')]]")
))
driver.execute_script("arguments[0].click();", date_btn)
print("✅ Date picker opened")
time.sleep(1.5)

# ── SELECT TODAY ──────────────────────────────────────────────────────────────
today_cell = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//button[starts-with(@aria-label,'Today,')]")
))
driver.execute_script("arguments[0].click();", today_cell)
print(f"✅ Selected date: {today_str}")
time.sleep(1)

# ── CLICK CONTINUE ────────────────────────────────────────────────────────────
continue_btn = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//button[contains(text(),'Continue') or contains(text(),'Next')]")
))
driver.execute_script("arguments[0].click();", continue_btn)
print("✅ Continue clicked")
time.sleep(3)

# ── DUPLICATE GUARD ───────────────────────────────────────────────────────────
page = driver.page_source.lower()
if "already submitted" in page or "already exist" in page:
    print("⚠️ Entry already exists for today. Skipping.")
    driver.quit()
    sys.exit(0)

# ── FILL FORM ─────────────────────────────────────────────────────────────────
work_summary = wait.until(EC.presence_of_element_located(
    (By.XPATH, "//textarea[@placeholder='Briefly describe the work you did today\u2026']")
))
print("✅ Diary form loaded")

work_summary.click()
work_summary.send_keys(SUMMARY)

links_box = driver.find_element(
    By.XPATH, "//textarea[@placeholder='Paste one or more relevant links, separated by commas']"
)
links_box.click()
if LINKS:
    links_box.send_keys(LINKS)

learning_box = driver.find_element(
    By.XPATH, "//textarea[@placeholder='What did you learn or ship today?']"
)
learning_box.click()
learning_box.send_keys(LEARNING)

blockers_box = driver.find_element(
    By.XPATH, "//textarea[@placeholder='Anything that slowed you down?']"
)
blockers_box.click()
blockers_box.send_keys(BLOCKERS)

# ── SKILLS ────────────────────────────────────────────────────────────────────
for skill in SKILLS:
    skills_input = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[contains(@id,'react-select')]")
    ))
    skills_input.click()
    skills_input.send_keys(skill)
    time.sleep(1)
    skills_input.send_keys(Keys.RETURN)
    time.sleep(0.8)

print("✅ Skills added")

# ── SAVE ──────────────────────────────────────────────────────────────────────
save_button = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//button[contains(text(),'Save')]")
))
driver.execute_script("arguments[0].click();", save_button)
print("✅ Diary entry submitted successfully!")
time.sleep(3)
driver.quit()