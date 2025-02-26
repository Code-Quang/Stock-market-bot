import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_first_10k_link(ticker):
    """
    Scrapes the first 10-K report link for a given stock ticker from SEC.gov.
    Returns a single URL or None if no link is found.
    """
    sec_url = "https://www.sec.gov/search-filings"

    # Set up Selenium WebDriver with headless configuration
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Set a custom User-Agent
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        })
        
        driver.get(sec_url)
        wait = WebDriverWait(driver, 15)

        time.sleep(3)

        # Locate search box and enter ticker
        search_box = wait.until(EC.presence_of_element_located((By.ID, "edgar-company-person")))
        search_box.clear()
        search_box.send_keys(ticker)
        time.sleep(2)

        # Wait for and select dropdown option
        first_option = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "tr")))
        driver.execute_script("arguments[0].click();", first_option)
        time.sleep(3)

        # Click on "10-K & 10-Q" section
        ten_k_section = wait.until(EC.presence_of_element_located((By.XPATH, "//h5[contains(., '10-K')]")))
        driver.execute_script("arguments[0].click();", ten_k_section)
        time.sleep(2)

        # Click "View all"
        view_all_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'View all 10-Ks and 10-Qs')]")))
        driver.execute_script("arguments[0].click();", view_all_button)
        time.sleep(3)

        # Locate first available 10-K report link
        report_link = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "document-link")))
        first_link = report_link.get_attribute("href") if report_link else None

        if first_link:
            print(f"Found 10-K report for {ticker}: {first_link}")
        else:
            print(f"No 10-K reports found for {ticker}")

        return first_link

    except Exception as e:
        print(f"Error fetching 10-K filings for {ticker}: {e}")
        return None

    finally:
        driver.quit()

# Read companies and tickers from CSV
companies = []
tickers = []

with open("companies.csv", mode="r", encoding="utf-8") as file:
    reader = csv.reader(file)
    for row in reader:
        for entry in row:
            match = re.match(r"(.+?)\s\((\w+)\)", entry.strip())
            if match:
                company_name, ticker = match.groups()
                companies.append(company_name)
                tickers.append(ticker)

# Write only the first link per company to CSV
with open("10k_links.csv", "w", newline="") as file:
    writer = csv.writer(file)

    for company, ticker in zip(companies, tickers):
        link = get_first_10k_link(ticker)
        print('link:',link)
        if link:  # Save only if a link is found
            writer.writerow([company, ticker, link])
