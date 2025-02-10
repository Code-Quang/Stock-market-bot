from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from fake_useragent import UserAgent

ua = UserAgent()

# Configure Selenium WebDriver
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# Set up WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def google_search(query, max_links=5):
    chrome_options.add_argument(f"user-agent={ua.random}")   

    """
    Perform a Google search and extract the top search result links.
    """
    driver.get("https://www.google.com/")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    
    time.sleep(3)  # Allow results to load

    links = []
    search_results = driver.find_elements(By.XPATH, '//a[h3]')
    
    for result in search_results[:max_links]:
        links.append(result.get_attribute("href"))
    
    return links

def scrape_page(url):
    """
    Extract text from a webpage, handling popups and cookie banners only if necessary.
    """
    if not url or not isinstance(url, str):
        print(f"Invalid URL: {url}")
        return ""

    driver.get(url)
    time.sleep(3)  # Allow the page to load

    # First attempt to extract text without handling popups
    paragraphs = driver.find_elements(By.TAG_NAME, "p")
    text_content = " ".join([p.text for p in paragraphs if p.text.strip()])
    
    # If the text content is sufficient, return it
    if len(text_content) > 200:
        return text_content

    # If text content is insufficient, handle cookies and popups
    print(f"Insufficient text extracted from {url}. Handling cookies and popups...")

    # Handle Cookie Banners
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
                print(f"Accepted cookies on {url}")
                time.sleep(2)  # Allow changes to take effect
                break  
        except:
            continue  

    # Detect and close popups
    popup_selectors = [
        'iframe',
        'div[aria-hidden="false"]',  
        'div[class*="popup"]',  
        'div[class*="overlay"]',  
        'div[class*="modal"]',  
        'button[aria-label="Close"]',
        'button[class*="close"]',
    ]
    
    popups = driver.find_elements(By.CSS_SELECTOR, ",".join(popup_selectors))

    if popups:
        print(f"Popup detected on {url}, attempting to close...")

        for popup in popups:
            try:
                popup.click()  
                time.sleep(2)  
                print("Popup closed.")
                break  
            except:
                print("Failed to close popup.")
    
    # Check for lingering popups
    popups = driver.find_elements(By.CSS_SELECTOR, ",".join(popup_selectors))
    if popups:  
        print(f"Popup on {url} cannot be closed. Skipping...")
        return ""  

    # Detect popups using keyword analysis
    page_text = driver.page_source.lower()
    popup_keywords = [
        "get full access", "subscribe to continue", "sign in to read", 
        "log in to access", "continue with google", "create a free account",
        "start your free trial", "already have an account", "register to read more"
    ]
    
    if any(keyword in page_text for keyword in popup_keywords):
        print(f"Popup-like text found on {url}. Skipping...")
        return ""  

    # Extract text again after handling popups and cookies
    paragraphs = driver.find_elements(By.TAG_NAME, "p")
    text_content = " ".join([p.text for p in paragraphs if p.text.strip()])
    
    return text_content
def google_search(query, max_links=10):
    """
    Perform a Google search and extract up to max_links search result links.
    Ensures at least 5 valid pages are scraped.
    """
    driver.get("https://www.google.com/")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    
    time.sleep(3)  # Allow results to load

    links = []
    search_results = driver.find_elements(By.XPATH, '//a[h3]')
    
    for result in search_results:
        href = result.get_attribute("href")
        if href and "google.com" not in href:  # Avoid Google-related links
            links.append(href)
    
    return links[:max_links]

def main():
    company_name = "MeridianLink Inc. (MLNK)"
    
    queries = [
        f"{company_name} financial and market analysis",  # More analysis-based query
        f"{company_name} competitors and market trends"
    ]

    results = []
    
    for query in queries:
        print(f"Searching for: {query}")
        links = google_search(query, max_links=10)  

        valid_results = 0
        for link in links:
            if valid_results >= 5:
                break  
            
            print(f"Scraping: {link}")
            text = scrape_page(link)
            print(f"text: {text}")
            print(f"len(text): {len(text)}")

            print('valid_results:', valid_results)
            
            if len(text) > 200:  # Save only valid results
                results.append({"Query": query, "URL": link, "Extracted Text": text})
                valid_results += 1

    # Save results to CSV
    df = pd.DataFrame(results)
    df.to_csv("mlnk_data.csv", index=False)
    
    print("Scraping complete. Data saved to mlnk_data.csv.")
    driver.quit()

if __name__ == "__main__":
    main()
