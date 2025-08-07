from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# ----------------------- Portal Detection ----------------------- #
def detect_portal(url):
    if "workable.com" in url:
        return "workable"
    elif "greenhouse.io" in url:
        return "greenhouse"
    elif "lever.co" in url:
        return "lever"
    elif "linkedin.com" in url:
        return "linkedin"
    elif url.startswith("file://") or "felig_form.html" in url:
        return "felig"
    else:
        return "unsupported"

# ----------------------- Workable Handler ----------------------- #
def apply_to_workable(driver, url, resume_path, user_info):
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        wait.until(EC.presence_of_element_located((By.NAME, "candidate[first_name]"))).send_keys(user_info['first_name'])
        driver.find_element(By.NAME, "candidate[last_name]").send_keys(user_info['last_name'])
        driver.find_element(By.NAME, "candidate[email]").send_keys(user_info['email'])
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(resume_path)

        try:
            driver.find_element(By.NAME, "candidate[cover_letter]").send_keys(user_info['cover_letter'])
        except NoSuchElementException:
            print("ℹ️ No cover letter field present on Workable.")

        print("✅ Workable form filled (but not submitted)")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Error applying to Workable: {e}")

# ----------------------- Greenhouse Handler ----------------------- #
def apply_to_greenhouse(driver, url, resume_path, user_info):
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        wait.until(EC.presence_of_element_located((By.ID, "first_name"))).send_keys(user_info['first_name'])
        driver.find_element(By.ID, "last_name").send_keys(user_info['last_name'])
        driver.find_element(By.ID, "email").send_keys(user_info['email'])
        driver.find_element(By.ID, "resume").send_keys(resume_path)

        try:
            driver.find_element(By.ID, "job_application_cover_letter").send_keys(user_info['cover_letter'])
        except NoSuchElementException:
            print("ℹ️ No cover letter field present on Greenhouse.")

        print("✅ Greenhouse form filled (but not submitted)")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Error applying to Greenhouse: {e}")

# ----------------------- Lever Handler ----------------------- #
def apply_to_lever(driver, url, resume_path, user_info):
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        wait.until(EC.presence_of_element_located((By.NAME, "name"))).send_keys(f"{user_info['first_name']} {user_info['last_name']}")
        driver.find_element(By.NAME, "email").send_keys(user_info['email'])
        driver.find_element(By.NAME, "phone").send_keys(user_info.get('phone', '123-456-7890'))
        driver.find_element(By.NAME, "resume").send_keys(resume_path)

        try:
            driver.find_element(By.NAME, "comments").send_keys(user_info['cover_letter'])
        except NoSuchElementException:
            print("ℹ️ No cover letter field present on Lever.")

        print("✅ Lever form filled (but not submitted)")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Error applying to Lever: {e}")

# ----------------------- LinkedIn Handler ----------------------- #
def apply_to_linkedin(driver, url, resume_path, user_info):
    driver.get(url)
    print("🔐 LinkedIn support requires login and additional steps. Skipped for now.")
    time.sleep(5)

# ----------------------- Felig Local Form Handler ----------------------- #
def apply_to_felig(driver, url, resume_path, user_info):
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        wait.until(EC.presence_of_element_located((By.NAME, "firstname"))).send_keys(user_info['first_name'])
        driver.find_element(By.NAME, "lastname").send_keys(user_info['last_name'])
        driver.find_element(By.NAME, "email").send_keys(user_info['email'])
        driver.find_element(By.ID, "resumeUpload").send_keys(resume_path)
        driver.find_element(By.NAME, "message").send_keys(user_info['cover_letter'])

        print("✅ Felig form filled successfully (not submitted)")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Error filling Felig form: {e}")

# ----------------------- Main Router ----------------------- #
def route_application(url, resume_path, user_info):
    portal = detect_portal(url)
    driver = webdriver.Chrome()

    try:
        if portal == "workable":
            apply_to_workable(driver, url, resume_path, user_info)
        elif portal == "greenhouse":
            apply_to_greenhouse(driver, url, resume_path, user_info)
        elif portal == "lever":
            apply_to_lever(driver, url, resume_path, user_info)
        elif portal == "linkedin":
            apply_to_linkedin(driver, url, resume_path, user_info)
        elif portal == "felig":
            apply_to_felig(driver, url, resume_path, user_info)
        else:
            print(f"❌ Unsupported job portal: {url}")
    finally:
        driver.quit()

# ----------------------- Sample Run ----------------------- #
if __name__ == '__main__':
    sample_user_info = {
        "first_name": "Sarah",
        "last_name": "Tadesse",
        "email": "sarah.tadesse@example.com",
        "cover_letter": "This is a test cover letter generated for a job application bot."
    }
    resume_path = os.path.abspath("data/user_resume.pdf")
    sample_url = "file:///C:/Users/user/Desktop/felig_form.html"  # Replace with your actual path

    route_application(sample_url, resume_path, sample_user_info)
