import os
import time
import json
import re
import datetime
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlparse

# Configure Selenium WebDriver for headless mode
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless=new")  # Run in headless mode
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d")

def clean_text(text):
    """Cleans extracted text by removing unnecessary content."""
    if not text:
        return ""

    text = re.sub(r'\s+', ' ', text).strip()

    irrelevant_phrases = [
        "sign up", "subscribe to continue", "get full access",
        "create a free account", "already have an account",
        "log in to access", "start your free trial", "cookie policy"
    ]
    for phrase in irrelevant_phrases:
        text = text.replace(phrase, '')

    return text

def extract_source_name(url):
    """Extracts the domain name from a URL."""
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace("www.", "")

def scrape_page(url, retries=3):
    """Extracts text from a webpage while handling popups and cookies."""
    if not url or not isinstance(url, str):
        return ""

    for attempt in range(retries):
        try:
            driver.get(url)
            time.sleep(3)

            page_date = CURRENT_DATE  # Default to today if no date is found
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            text_content = " ".join([p.text for p in paragraphs if p.text.strip()])
            text_content = clean_text(text_content)

            return page_date, text_content if len(text_content) > 200 else ""

        except TimeoutException:
            print(f"Timeout while loading {url}. Retrying... (Attempt {attempt + 1})")
            if attempt == retries - 1:
                return CURRENT_DATE, ""
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return CURRENT_DATE, ""

def main():
    results = []

    # Read extracted links from the CSV file
    with open("extracted_links.csv", mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        links = [row[0] for row in reader]

    for link in links:
        print(f"Scraping: {link}")
        page_date, text = scrape_page(link)
        if len(text) > 1000:
            source_name = extract_source_name(link)

            result = {
                "Date": page_date,
                "Source Name": source_name,
                "Source URL": link,
                "Extracted Text": text
            }
            results.append(result)

    # Save results to JSON files
    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("Scraping complete. Data saved to scraped_data.json.")
    driver.quit()

if __name__ == "__main__":
    main()
