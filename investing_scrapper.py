from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium_stealth import stealth

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

stealth(driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)
def scrape_investing(search_terms):
    driver = webdriver.Chrome()  # Ensure you have chromedriver installed
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://www.investing.com/")
        time.sleep(2)  # Allow page to load

        for term in search_terms:
            # Locate the search box and enter search term
            search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q']")))
            search_box.clear()
            search_box.send_keys(term)
            search_box.send_keys(Keys.RETURN)  # Press Enter
            
            # Wait for the results section to appear
            search_results_section = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "searchSectionMain")))

            # Get the first 3 URLs from the search results
            article_links = search_results_section.find_elements(By.CSS_SELECTOR, "a")[:3]
            article_urls = [link.get_attribute("href") for link in article_links if link.get_attribute("href")][:3]

            scraped_data = []

            for url in article_urls:
                driver.get(url)
                time.sleep(2)

                # Extract article content
                article_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))).text
                scraped_data.append(f"URL: {url}\n\n{article_text}\n\n{'-'*50}\n")

                # Go back to the search results page
                driver.back()
                time.sleep(2)

            # Save scraped data to a text file
            with open(f"{term.replace(' ', '_')}_articles.txt", "w", encoding="utf-8") as file:
                file.writelines(scraped_data)

    finally:
        driver.quit()

# Run the function with a list of search terms
scrape_investing(["MeridianLink Inc"])
