import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import datetime
import csv
from urllib.parse import urlparse
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
import random

# Configure Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# chrome_options.add_argument("--headless=new")  # Ensures headless mode works properly
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
driver.set_page_load_timeout(60)  # Increase from 30 to 60 seconds

CURRENT_YEAR = datetime.datetime.now().year
CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
FIVE_DAYS_AGO = (datetime.datetime.now() - datetime.timedelta(days=5)).date()

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

def search_google(query, max_links=5):
    """Fetch search result URLs using Google Search via Selenium."""
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    driver.get(search_url)
    time.sleep(random.uniform(3, 6))

    try:
        search_results = driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf a")
        links = [result.get_attribute("href") for result in search_results if result.get_attribute("href")]

        valid_links = [link for link in links if "google.com" not in link]
        if len(valid_links) < max_links:
            print(f"Only found {len(valid_links)} valid links for: {query}")

        return valid_links[:max_links]

    except NoSuchElementException:
        print(f"No results found for query: {query}")
        return []

def extract_source_name(url):
    """Extracts the domain name from a URL."""
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace("www.", "")

def handle_cookies_and_popups():
    """Handles cookie consent popups and overlays."""
    button_selectors = [
        'button:contains("Accept all")', 'button:contains("Accept cookies")', 'button:contains("accept")',
        'button:contains("I agree")', 'button[aria-label="Accept"]',
        'button[class*="cookie"]', 'div[class*="cookie"] button'
    ]
    try:
        for selector in button_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    element.click()
                    time.sleep(2)
                    return  
    except:
        pass

def extract_date_from_page():
    """Extracts the first date found on the webpage. Defaults to today if none is found."""
    try:
        page_text = driver.page_source
        date_patterns = [
            r'(\b\d{1,2} [A-Za-z]+ \d{4}\b)',  # e.g., 12 March 2023
            r'(\b[A-Za-z]+ \d{1,2}, \d{4}\b)',  # e.g., March 12, 2023
            r'(\b\d{4}-\d{2}-\d{2}\b)',  # e.g., 2023-03-12
        ]

        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                extracted_date = datetime.datetime.strptime(match.group(0), "%Y-%m-%d").date() if '-' in match.group(0) else datetime.datetime.strptime(match.group(0), "%d %B %Y").date()
                if extracted_date < FIVE_DAYS_AGO:
                    return CURRENT_DATE
                return str(extracted_date)

        return CURRENT_DATE  # Default to today if no date is found
    except:
        return CURRENT_DATE

def scrape_page(url, retries=3):
    """Extracts text from a webpage while handling popups and cookies."""
    if not url or not isinstance(url, str):
        return ""

    for attempt in range(retries):
        try:
            driver.set_page_load_timeout(60)  # Increase timeout
            driver.get(url)
            time.sleep(3)

            handle_cookies_and_popups()

            page_date = extract_date_from_page()

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
    companies, tickers = [], []
    with open("companies.csv", mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            for entry in row:
                match = re.match(r"(.+?)\s\((\w+)\)", entry.strip())
                if match:
                    company_name, ticker = match.groups()
                    companies.append(company_name)
                    tickers.append(ticker)

    base_queries = [
        "{company} quarterly earnings report",
        "{company} annual report filetype:pdf",
        "{company} stock analysis site:fool.com OR site:thestreet.com",
        "{company} competitors and market share",
        "{company} stock forecast {year}",
        "{ticker} stock technical analysis",
        "{company} transcript of an earnings call",  # New Query 1
        "{company} an analyst report from an investment bank or research firm"  # New Query 2
    ]

    results = []
    earnings_call_results = []
    analyst_report_results = []
    source_list = set()

    for company, ticker in zip(companies, tickers):
        print(f"\n=== Searching for: {company} ({ticker}) ===\n")

        queries = [query.format(company=company, ticker=ticker, year=CURRENT_YEAR) for query in base_queries]

        for query in queries:
            time.sleep(random.uniform(10, 20))

            print(f"Searching: {query}")
            links = search_google(query, max_links=5)

            valid_results = 0
            for link in links:
                if valid_results >= 5:
                    break

                print(f"Scraping: {link}")
                page_date, text = scrape_page(link)

                if len(text) > 1000:
                    source_name = extract_source_name(link)
                    source_list.add(source_name)

                    result = {
                        "Date": page_date,
                        "Headline": query,
                        "Source Name": source_name,
                        "Source URL": link,
                        "Extracted Text": text
                    }
                    results.append(result)
                    valid_results += 1

                    # Separate handling for the new queries
                    if "transcript of an earnings call" in query:
                        earnings_call_results.append(result)
                    elif "analyst report from an investment bank or research firm" in query:
                        analyst_report_results.append(result)

                else:
                    print("Skipping due to insufficient content.")

    # Save results to JSON files
    with open("stock_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    with open("earnings_calls.json", "w", encoding="utf-8") as f:
        json.dump(earnings_call_results, f, indent=4)

    with open("analyst_reports.json", "w", encoding="utf-8") as f:
        json.dump(analyst_report_results, f, indent=4)

    with open("source_index.json", "w", encoding="utf-8") as f:
        json.dump(list(source_list), f, indent=4)

    print("\nScraping complete. Data saved to stock_data.json, earnings_calls.json, analyst_reports.json, and source_index.json.")
    driver.quit()

if __name__ == "__main__":
    main()
