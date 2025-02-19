import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Initialize Selenium WebDriver (Head Mode)
def init_driver():
    options = Options()
    options.add_argument("start-maximized")  # Open in full screen
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Function to perform Google search and extract top result links
def google_search_links(driver, query):
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    driver.get(search_url)
    time.sleep(3)  # Allow time for results to load

    links = []
    search_results = driver.find_elements(By.CSS_SELECTOR, "a[href^='http']")

    for result in search_results:
        link = result.get_attribute("href")
        if "google" not in link and link not in links:  # Avoid Google-related links
            links.append(link)
        if len(links) >= 10:  # Limit to top 10 results
            break

    return links

# Main function to extract links for specific queries
def extract_links(input_file, output_file):
    driver = init_driver()

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    extracted_links = {}

    for company, competitors in data.items():
        extracted_links[company] = []

        # Limit processing to first 5 competitors
        for competitor in competitors[:5]:
            name = competitor.get("name")
            ticker = competitor.get("ticker")

            print(f"Extracting links for {name} ({ticker})...")

            competitor_data = {
                "name": name,
                "ticker": ticker,
                "products_and_services": google_search_links(driver, f"{name} products and services"),
                "primary_markets": google_search_links(driver, f"{name} primary markets"),
                "submarkets": google_search_links(driver, f"{name} submarkets"),
                "market_size_units": google_search_links(driver, f"{name} market size in units"),
                "market_size_dollars": google_search_links(driver, f"{name} market size in dollars"),
                "growth_forecast": google_search_links(driver, f"{name} growth forecast"),
                "key_positive_factors": google_search_links(driver, f"{name} key positive factors affecting growth"),
                "key_negative_factors": google_search_links(driver, f"{name} key negative factors affecting growth"),
            }

            extracted_links[company].append(competitor_data)
            time.sleep(2)  # Pause to prevent bot detection

    driver.quit()

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_links, f, ensure_ascii=False, indent=4)

    print(f"Extracted links saved to {output_file}.")

# Run the script for the first 5 competitors
input_json_file = './competitors/cleaned_competitors.json'
output_json_file = './competitors/extracted_links.json'
extract_links(input_json_file, output_json_file)
