import os
import time
import json
import re
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse

# Configure Selenium WebDriver for headless mode
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless=new")
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
        return CURRENT_DATE, ""

    driver.set_page_load_timeout(60)  # Set timeout for page loading

    for attempt in range(retries):
        try:
            driver.get(url)
            time.sleep(3)  # Wait for the page to load

            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            text_content = " ".join([p.text for p in paragraphs if p.text.strip()])
            text_content = clean_text(text_content)

            return CURRENT_DATE, text_content  # Return date and cleaned text

        except TimeoutException:
            print(f"Timeout while loading {url}. Retrying... (Attempt {attempt + 1})")
            time.sleep(2)  # Wait before retrying
            if attempt == retries - 1:
                return CURRENT_DATE, ""
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return CURRENT_DATE, ""


def main():
    results = []

    # Read extracted links from the JSON file
    with open("./competitors/extracted_links.json", mode="r", encoding="utf-8") as file:
        data = json.load(file)

    # Get the first company and its competitors
    for company_name, competitors in list(data.items())[:5]:  # Select the first company only
        print(f"Processing competitors for company: {company_name}")

        # Limit to first 5 competitors
        selected_competitors = competitors[:5]

        for competitor in selected_competitors:
            name = competitor.get("name")
            ticker = competitor.get("ticker")

            # Get all link fields
            all_link_fields = ["products_and_services", "primary_markets", "submarkets", "market_size_units", "market_size_dollars"]

            for field in all_link_fields:
                links = competitor.get(field, [])
                successful_scrapes = 0

                for link in links:
                    if successful_scrapes >= 3:
                        break  # Stop scraping this field after 3 successful scrapes

                    print(f"Scraping: {link} for {name} ({ticker}) - {field}")
                    page_date, text = scrape_page(link)

                    if len(text) > 1000:  # Check if text is successful (> 1000 chars)
                        source_name = extract_source_name(link)

                        result = {
                            "Date": page_date,
                            "Source Name": source_name,
                            "Source URL": link,
                            "Extracted Text": text,
                            "Company Name": name,
                            "Ticker": ticker,
                            "Field": field,
                            "Parent Company": company_name  # Add context about which company the competitor belongs to
                        }
                        results.append(result)
                        successful_scrapes += 1

    # Save results to JSON file
    with open("./competitors/competitors_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("Scraping complete. Data saved to competitors_data.json.")
    driver.quit()


if __name__ == "__main__":
    main()
