from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import datetime
from googlesearch import search
import csv
import re
from selenium.common.exceptions import TimeoutException

# Configure Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--headless")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Define the list of companies and their tickers


# Get the current year dynamically
CURRENT_YEAR = datetime.datetime.now().year

def clean_text(text):
    """Cleans the extracted text by removing irrelevant content."""
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

def search_google_with_library(query, max_links=5):
    """Uses the googlesearch library to fetch search result URLs."""
    links = []
    try:
        for url in search(query, num_results=max_links, timeout=10):
            if "google.com" not in url:  # Avoid Google-related links
                links.append(url)
    except Exception as e:
        print(f"Error fetching Google search results: {e}")
    return links

def handle_cookies_and_popups():
    """Handles cookie consent popups and overlays on a webpage."""
    cookie_selectors = [
        'button:contains("Accept all")', 
        'button:contains("Accept cookies")', 
        'button:contains("I agree")',
        'button[aria-label="Accept"]',
        'button[class*="cookie"]',
        'div[class*="cookie"] button'
    ]

    for selector in cookie_selectors:
        try:
            cookie_button = driver.find_element(By.CSS_SELECTOR, selector)
            if cookie_button.is_displayed():
                cookie_button.click()
                time.sleep(2)
                break  
        except:
            continue  

    popup_selectors = [
        'iframe', 'div[aria-hidden="false"]', 'div[class*="popup"]', 
        'div[class*="overlay"]', 'div[class*="modal"]', 
        'button[aria-label="Close"]', 'button[class*="close"]',
    ]

    popups = driver.find_elements(By.CSS_SELECTOR, ",".join(popup_selectors))

    if popups:
        for popup in popups:
            try:
                popup.click()
                time.sleep(2)
                break  
            except:
                continue  


def scrape_page(url):
    """Extracts text from a webpage while handling popups and cookies."""
    if not url or not isinstance(url, str):
        return ""

    try:
        driver.set_page_load_timeout(30)  # Set a timeout for page load
        driver.get(url)
        time.sleep(3)

        handle_cookies_and_popups()

        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        text_content = " ".join([p.text for p in paragraphs if p.text.strip()])

        text_content = clean_text(text_content)

        return text_content if len(text_content) > 200 else ""

    except TimeoutException:
        print(f"Timeout occurred while loading {url}. Skipping to the next URL.")
        return ""

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def main(): 
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

    
    base_queries = [
        "{company} quarterly earnings report site:businesswire.com",
        "{company} annual report filetype:pdf",
        "{company} stock analysis report site:fool.com OR site:thestreet.com",
        "{company} competitors and market share",
        "{company} stock forecast {year}", 
        "{ticker} stock technical analysis",  
    ]

    results = []

    for company, ticker in zip(companies, tickers):
        print(f"\n=== Searching for: {company} ({ticker}) ===\n")

        queries = [query.format(company=company, ticker=ticker, year=CURRENT_YEAR) for query in base_queries]

        for query in queries:
            print(f"Searching: {query}")
            links = search_google_with_library(query, max_links=10)

            valid_results = 0
            for link in links:
                if valid_results >= 3:
                    break  

                print(f"Scraping: {link}")
                text = scrape_page(link)

                if len(text) > 200:
                    print('text:',text)
                    print('valid_results:',valid_results)

                    results.append({"Company": company, "Query": query, "URL": link, "Extracted Text": text})
                    valid_results += 1

                else:
                    print("Skipping due to insufficient content.")
                # time.sleep(random.uniform(3, 6))  

    with open("stock_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\nScraping complete. Data saved to stock_data.json.")
    driver.quit()

if __name__ == "__main__":
    main()
