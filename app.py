from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
 
def get_company_stock_info(company_name):
    """
    Searches Google for the company's stock information.
    Returns the stock ticker if found, otherwise None.
    """
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # Perform Google search
        search_url = f"https://www.google.com/search?q={company_name} stock"
        driver.get(search_url)
        time.sleep(3)  # Allow page to load

        # Locate ticker symbol (Google usually displays it in a span tag near stock price)
        try:
            ticker = driver.find_element(By.XPATH, "//span[contains(text(), '(')]").text
        except:
            ticker = None  # Not found

        return {
            "company_name": company_name,
            "ticker": ticker
        }
    
    except Exception as e:
        print(f"Error fetching stock info for {company_name}: {e}")
        return None
    
    finally:
        driver.quit()


def get_sec_filings(ticker, filing_type="10-K"):
    """
    Scrapes the latest SEC 10-K filing URL for the given stock ticker.
    Downloads the full report (HTML format).
    """
    # SEC EDGAR search URL
    sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={filing_type}&count=10&output=atom"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(sec_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch SEC filings for {ticker}")
        return None

    # Parse the XML response
    soup = BeautifulSoup(response.text, "xml")
    entries = soup.find_all("entry")

    if not entries:
        print(f"No {filing_type} found for {ticker}")
        return None

    # Extract the latest filing document link
    latest_filing_url = entries[0].find("link")["href"]
    filing_page_url = f"https://www.sec.gov{latest_filing_url}"

    # Fetch the filing page
    filing_page = requests.get(filing_page_url, headers=headers)
    filing_soup = BeautifulSoup(filing_page.text, "html.parser")

    # Find the full filing document (usually the first one)
    report_link = filing_soup.find("a", text="10-K")
    if report_link:
        full_filing_url = f"https://www.sec.gov{report_link['href']}"
        print(f"Downloading 10-K for {ticker}: {full_filing_url}")

        # Save the HTML filing
        os.makedirs("sec_filings", exist_ok=True)
        file_path = f"sec_filings/{ticker}_10K.html"

        with open(file_path, "w", encoding="utf-8") as f:
            filing_content = requests.get(full_filing_url, headers=headers).text
            f.write(filing_content)
        
        print(f"Saved: {file_path}")
        return full_filing_url
    else:
        print(f"No direct 10-K link found for {ticker}")
        return None

def get_all_10k_links(ticker):
    """
    Scrapes all 10-K report links for a given stock ticker from SEC.gov.
    Returns a list of URLs.
    """
    sec_url = "https://www.sec.gov/search-filings"
    
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(sec_url)
        wait = WebDriverWait(driver, 10)

        # Locate search box and enter ticker
        search_box = wait.until(EC.presence_of_element_located((By.ID, "edgar-company-person")))
        search_box.send_keys(ticker)
        time.sleep(2)  # Wait for dropdown to load

        dropdown_table = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "smart-search-entity-hints")))

        # Click the first row in the dropdown table
        first_option = dropdown_table.find_element(By.TAG_NAME, "tr")
        first_option.click()
        time.sleep(3)  # Allow navigation to company page


        # Click on "10-K & 10-Q" section
        ten_k_section = wait.until(EC.element_to_be_clickable((By.XPATH, "//h5[contains(., '10-K')]")))
        print('ten_k_section:',ten_k_section)
        ten_k_section.click()
        time.sleep(2)

        # Click on "View all 10-Ks and 10-Qs"
        view_all_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View all 10-Ks and 10-Qs')]")))
        view_all_button.click()
        time.sleep(3)

        # Find the "dataTables_scroll" div
        scroll_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dataTables_scroll")))

        # Extract all 10-K document links
        report_links = scroll_div.find_elements(By.CLASS_NAME, "document-link")
        links = [link.get_attribute("href") for link in report_links]

        print(f"Found {len(links)} 10-K reports for {ticker}")
        return links
    
    except Exception as e:
        print(f"Error fetching 10-K filings for {ticker}: {e}")
        return []
    
    finally:
        driver.quit()

# Example usage
# companies = ["MeridianLink Inc.", "PagerDuty Inc.", "Amplitude Inc."]
tickers = ["MLNK", "PD", "AMPL", "CMPO", "WEAV", "VNET", "EGHT"]
tickers = ["MLNK"]

with open("10k_links.csv", "a", newline="") as file:
    writer = csv.writer(file)

    for ticker in tickers:
        links = get_all_10k_links(ticker)
        print("links:", links)

        for link in links:
            writer.writerow([ticker, link]) 


