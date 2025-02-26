import os
import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random
import datetime

# Configure Selenium WebDriver for head mode
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def search_google(query, max_links=5):
    """Fetch search result URLs using Google Search via Selenium."""
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    driver.get(search_url)
    time.sleep(random.uniform(3, 6))

    search_results = driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf a")
    links = [result.get_attribute("href") for result in search_results if result.get_attribute("href")]
    valid_links = [link for link in links if "google.com" not in link]

    return valid_links[:max_links]

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
        "{company} transcript of an earnings call",
        "{company} an analyst report from an investment bank or research firm"
    ]

    results = []

    for company, ticker in zip(companies, tickers):
        print(f"\n=== Searching for: {company} ({ticker}) ===\n")
        queries = [query.format(company=company, ticker=ticker, year=datetime.datetime.now().year) for query in base_queries]

        for query in queries:
            time.sleep(random.uniform(10, 20))
            print(f"Searching: {query}")
            links = search_google(query, max_links=5)
            results.extend(links)

    # Save results to a CSV file
    with open("extracted_links.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows([[link] for link in results])

    print("Link extraction complete. Data saved to extracted_links.csv.")
    driver.quit()

if __name__ == "__main__":
    main()
