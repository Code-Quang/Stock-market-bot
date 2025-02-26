from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import re
import csv
def clean_article_content(text):
    """Clean and format article content by removing financial tables and unwanted patterns."""
    # Remove financial statement patterns
    patterns_to_remove = [
        r'\([^)]*thousands[^)]*\)',
        r'(?s)As of.*?Assets',
        r'(?s)Current assets:.*?Total current assets',
        r'(?s)Stockholders.[^ ]*\s*Equity:.*?Total stockholders.[^ ]*\s*equity',
        r'(?s)Condensed Consolidated Statements.*?\d{4}',
        r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?',  # Currency amounts
        r'\d{1,3}(?:,\d{3})*(?:\.\d+)?%?'  # Numbers and percentages
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text)
    
    # Remove multiple spaces and newlines
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text.strip()

def initialize_driver():
    """Initialize Chrome driver with headless mode and other options."""
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--headless') 
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def scrape_news_articles(driver, ticker, results_dict):
    """Scrape news articles for a given ticker and update results dictionary."""
    url = f"https://finance.yahoo.com/quote/{ticker}/news/"
    successful_scrapes = 0
    
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.stream-items"))
        )
    except Exception as e:
        print(f"Error loading page for {ticker}: {e}")
        return
    
    news_links = driver.find_elements(By.CSS_SELECTOR, "ul.stream-items li a")
    article_urls = {link.get_attribute('href') for link in news_links 
                   if link.get_attribute('href') and "https://finance.yahoo.com/news" in link.get_attribute('href')}
    
    results_dict[ticker] = []
    
    for url in article_urls:
        if successful_scrapes >= 5:
            break
            
        try:
            driver.get(url)
            
            try:
                continue_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Story Continues']]"))
                )
                continue_button.click()
            except:
                pass
            
            try:
                article_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
                article_content = article_element.text
                cleaned_content = clean_article_content(article_content)
                
                if len(cleaned_content) > 500:
                    # Get article title
                    try:
                        title = driver.find_element(By.CSS_SELECTOR, "h1").text
                    except:
                        title = "No title found"
                    
                    # Get publication date
                    try:
                        date = driver.find_element(By.CSS_SELECTOR, "time").get_attribute("datetime")
                    except:
                        date = "No date found"
                    
                    article_data = {
                        "url": url,
                        "title": title,
                        "date": date,
                        "content": cleaned_content
                    }
                    
                    results_dict[ticker].append(article_data)
                    successful_scrapes += 1
                    print(f"Successfully scraped article {successful_scrapes} for {ticker}")
            
            except Exception as e:
                print(f"Error extracting content from {url}: {e}")
                continue
                
        except Exception as e:
            print(f"Error accessing {url}: {e}")
    
    print(f"Completed scraping for {ticker}. Successfully scraped {successful_scrapes} articles.")

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

    # tickers = ["MLNK", "PD", "AMPL", "CMPO", "WEAV", "VNET", "EGHT"]
    results = {}
    
    driver = initialize_driver()
    
    try:
        for ticker in tickers:
            print(f"\nStarting to scrape {ticker}")
            scrape_news_articles(driver, ticker, results)
            
        # Write results to JSON file
        with open('yahoo_results_1.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main()