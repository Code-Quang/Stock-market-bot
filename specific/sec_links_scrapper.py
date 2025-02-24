# sec_links_scrapper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import time
import csv
import re

def get_all_10k_links(ticker, max_reports=3):
    """
    Scrapes all 10-K report links for a given stock ticker from SEC.gov.
    Returns a list of URLs. The function will stop after finding the specified number of reports per company.
    """
    
    sec_url = "https://www.sec.gov/search-filings"

    # Set up Selenium WebDriver with enhanced headless configuration
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Modern headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")  # Set a standard resolution
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Set a custom User-Agent
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        })

        driver.get(sec_url)
        wait = WebDriverWait(driver, 15)  # Increased wait time

        # Add a small initial delay to ensure page loads completely
        time.sleep(3)

        # Locate search box and enter ticker
        search_box = wait.until(EC.presence_of_element_located((By.ID, "edgar-company-person")))
        search_box.clear()
        search_box.send_keys(ticker)
        time.sleep(2)

        # Wait for and interact with dropdown
        dropdown_table = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "smart-search-entity-hints")))

        # Scroll the dropdown into view
        driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_table)

        first_option = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "tr")))
        driver.execute_script("arguments[0].click();", first_option)
        time.sleep(3)

        # Click on "10-K & 10-Q" section using JavaScript
        ten_k_section = wait.until(EC.presence_of_element_located((By.XPATH, "//h5[contains(., '10-K')]")))
        driver.execute_script("arguments[0].click();", ten_k_section)
        time.sleep(2)

        # Click "View all" using JavaScript
        view_all_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'View all 10-Ks and 10-Qs')]")))
        driver.execute_script("arguments[0].click();", view_all_button)
        time.sleep(3)

        # Find the scroll div and extract links
        scroll_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dataTables_scroll")))

        # Scroll through the div to load all content
        last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_div)
        while True:
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_div)
            time.sleep(2)
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_div)
            if new_height == last_height:
                break
            last_height = new_height

        # Extract links
        report_links = scroll_div.find_elements(By.CLASS_NAME, "document-link")
        links = [link.get_attribute("href") for link in report_links[:max_reports]]  # Limit to max_reports

        print(f"Found {len(links)} 10-K reports for {ticker}")
        return links

    except Exception as e:
        print(f"Error fetching 10-K filings for {ticker}: {e}")
        return []

    finally:
        driver.quit()

# Read companies from CSV
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

# Write links to CSV
with open("10k_links.csv", "a", newline="") as file:
    writer = csv.writer(file)

    for ticker in tickers:
        links = get_all_10k_links(ticker, max_reports=3)  # Set the maximum number of reports per company here
        print("links:", links)

        for link in links:
            writer.writerow([ticker, link])
