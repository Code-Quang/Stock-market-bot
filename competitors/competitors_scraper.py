import os
import time
import csv
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random
import datetime

# Configure Selenium WebDriver for headless mode
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

def extract_competitors(page_url):
    """Extract competitor names from the given page URL."""
    driver.get(page_url)
    time.sleep(random.uniform(3, 6))  # Wait for the page to load

    competitors = []
    elements = driver.find_elements(By.XPATH, "//body//p | //body//li | //body//h2 | //body//h3")

    for element in elements:
        text = element.text.strip()
        if any(keyword in text.lower() for keyword in ["competitors", "rivals", "similar companies", "competing companies"]):
            # Extract competitor names, assuming they might be listed in the same element or context
            competitors += [name.strip() for name in text.split(',') if name.strip()]

    return competitors

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

    # Updated query to search specifically for competitors
    results = {}

    for company, ticker in zip(companies, tickers):
        print(f"\n=== Searching for competitors of: {company} ({ticker}) ===\n")
        query = f"{company} competitors"
        
        time.sleep(random.uniform(10, 20))
        print(f"Searching: {query}")
        links = search_google(query, max_links=5)

        # Extract competitors from the links found
        competitors = set()  # Use a set to avoid duplicates
        for link in links:
            competitors.update(extract_competitors(link))

        results[company] = [{"name": competitor.split('(')[0].strip(), "ticker": competitor.split('(')[1].replace(')', '').strip() if '(' in competitor else ""} for competitor in competitors]

    # Save results to a JSON file
    with open("competitors.json", "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)

    print("Competitor extraction complete. Data saved to competitors.json.")
    driver.quit()

if __name__ == "__main__":
    main()
