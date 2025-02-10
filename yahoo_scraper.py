from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Initialize Chrome with SSL error ignoring
chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
driver = webdriver.Chrome(options=chrome_options)

# Set to track visited URLs
visited_urls = set()

# Function to scrape news articles
def scrape_news_articles(ticker):
    # Construct the URL
    url = f"https://finance.yahoo.com/quote/{ticker}/news/"
    
    # Open the URL
    driver.get(url)
    
    # Wait for the page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.stream-items"))
        )
    except Exception as e:
        print(f"Error loading page for {ticker}: {e}")
        return
    
    # Find all news article links
    news_links = driver.find_elements(By.CSS_SELECTOR, "ul.stream-items li a")
    
    # Extract URLs that match the required pattern
    article_urls = {link.get_attribute('href') for link in news_links 
                    if link.get_attribute('href') and "https://finance.yahoo.com/news" in link.get_attribute('href')}
    
    # Filter out already visited URLs
    new_article_urls = article_urls - visited_urls
    visited_urls.update(new_article_urls)

    # Save new URLs to a file
    with open(f"{ticker}_news_urls.txt", "w") as file:
        for url in new_article_urls:
            file.write(url + "\n")
    
    # Scrape each article
    for url in new_article_urls:
        print('url:',url)
        try:
            driver.get(url)
            
            # Check if "Story Continues" button exists and click it
            try:
                continue_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Story Continues']]"))
                )

                continue_button.click()
            except:
                print(f"No 'Story Continues' button found for {url}")
            
            # Wait for the article content to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
            except:
                print(f"Article content not found for {url}")
                continue
            
            # Scrape the article content
            article_content = driver.find_element(By.CSS_SELECTOR, "article").text
            
            # Save the scraped content to a file
            with open(f"{ticker}_news_articles.txt", "a") as file:
                file.write(f"URL: {url}\n")
                file.write(article_content + "\n\n")
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    
    print(f"Scraping completed for {ticker}")

# Example usage
# PD
ticker = "PD"

# ticker = "MLNK"
scrape_news_articles(ticker)

# Close the WebDriver
driver.quit()
