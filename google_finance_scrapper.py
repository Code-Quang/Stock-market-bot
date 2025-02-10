from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Set up the Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (remove for debugging)
driver = webdriver.Chrome(options=options)

try:
    # Open the Google Finance page
    url = "https://www.google.com/finance/quote/MLNK:NYSE?hl=en"
    driver.get(url)

    # Wait until the main content is loaded
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "main")))

    def scrape_tab(tab_name):
        try:
            # Wait for the tab element to be clickable
            tab_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{tab_name}')]"))
            )
            
            # Scroll into view before clicking
            driver.execute_script("arguments[0].scrollIntoView();", tab_element)

            # Click the tab
            ActionChains(driver).move_to_element(tab_element).click().perform()

            # Wait for new content to load
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "main")))

            # Extract and print the entire <main> tag content
            main_content = driver.find_element(By.TAG_NAME, "main")
            print(f"\nData for {tab_name}:\n")
            print(main_content.text)

        except Exception as e:
            print(f"Error scraping {tab_name}: {e}")

    # Scrape Balance Sheet and Cash Flow tabs
    scrape_tab("Balance Sheet")
    scrape_tab("Cash Flow")

finally:
    driver.quit()
