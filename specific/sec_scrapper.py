import csv  # For reading companies.csv
import requests
import json
import time
import pandas as pd
from datetime import datetime
import re
from typing import Dict, List, Any

def verify_companies():
    with open("companies.csv", mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            print(f"Processing row: {row}")
            
class CompanyAnalyzer:
    def __init__(self, user_agent: str = 'Company Name (email@domain.com)'):
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json',
            'Host': 'data.sec.gov'
        }
    
    def _format_cik(self, cik: str) -> str:
        """Format CIK to 10 digits with leading zeros"""
        return str(int(cik)).zfill(10)

    def get_company_facts(self, cik: str) -> Dict:
        """Get company facts including financial data"""
        cik_padded = self._format_cik(cik)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
        
        try:
            print(f"Requesting URL: {url}")
            time.sleep(0.1)  # SEC rate limit compliance
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching company facts: {e}")
            return None

    def get_company_info(self, cik: str) -> Dict:
        """Get company submission information"""
        cik_padded = self._format_cik(cik)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        
        try:
            print(f"Requesting URL: {url}")
            time.sleep(0.1)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching company info: {e}")
            return None

    def extract_latest_metrics(self, facts_data: Dict) -> Dict:
        """Extract the most recent values for key metrics from company facts"""
        if not facts_data or 'facts' not in facts_data:
            return {}

        essential_metrics = {
            'Revenue': 'Total revenue',
            'NetIncomeLoss': 'Net income/loss',
            'OperatingIncomeLoss': 'Operating income',
            'Assets': 'Total assets',
            'Liabilities': 'Total liabilities'
        }
        
        metrics = {}
        us_gaap_data = facts_data.get('facts', {}).get('us-gaap', {})
        
        for metric_key, metric_name in essential_metrics.items():
            if metric_key in us_gaap_data:
                metric_data = us_gaap_data[metric_key]
                if 'units' in metric_data:
                    # Usually 'USD' for financial values
                    unit_type = next(iter(metric_data['units']))
                    values = metric_data['units'][unit_type]
                    
                    # Filter for 10-K filings and get the most recent
                    annual_values = [v for v in values if v.get('form') == '10-K']
                    if annual_values:
                        latest = max(annual_values, key=lambda x: x.get('end', ''))
                        metrics[metric_name] = {
                            'value': latest.get('val'),
                            'date': latest.get('end'),
                            'unit': unit_type
                        }
        
        return metrics

def main():
    # 1. First verify companies
    verify_companies()
    print("=== Companies from verification ===")

    analyzer = CompanyAnalyzer(user_agent='Your Company Name (your.email@domain.com)')  
    
    # 2. Read and debug DataFrame
    try:
        df = pd.read_csv('10k_links.csv', header=None, names=['ticker', 'url'])
        print("=== Contents of 10k_links.csv ===")
        print(df.head())
        print(f"Total rows in DataFrame: {len(df)}")
        
        # 3. Check for duplicates
        unique_tickers = df['ticker'].unique()
        print(f"Unique tickers: {unique_tickers}")
        print(f"Total unique tickers: {len(unique_tickers)}")
        
        # 4. Remove duplicates
        df = df.drop_duplicates(subset=['ticker'])
        
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    company_data = {}
    processed_tickers = set()  # 5. Track processed companies

    # 6. Modified main processing loop
    for _, row in df.iterrows():
        ticker = row['ticker']
        print(f"=== Processing row {_} ===")
        print(f"Full row content: {row.to_dict()}")
        
        # Skip if already processed
        if ticker in processed_tickers:
            print(f"Skipping duplicate ticker: {ticker}")
            continue
        processed_tickers.add(ticker)
        
        time.sleep(1)  # Rate limiting
        cik_match = re.search(r'/edgar/data/(\d+)/', row['url'])
        
        if not cik_match:
            print(f"Could not extract CIK from URL for {ticker}")
            continue
            
        cik = cik_match.group(1)
        print(f"\nAnalyzing {ticker} (CIK: {cik})...")
        
        
        # Get company facts data
        facts_data = analyzer.get_company_facts(cik)
        if not facts_data:
            print(f"Could not retrieve data for {ticker}")
            continue
        
        # Get company info for latest filing date
        company_info = analyzer.get_company_info(cik)
        latest_10k_date = None
        if company_info and 'filings' in company_info:
            recent_filings = company_info['filings']['recent']
            for idx, form in enumerate(recent_filings.get('form', [])):
                if form == '10-K':
                    latest_10k_date = recent_filings['reportDate'][idx]
                    break
        
        # Extract metrics
        metrics = analyzer.extract_latest_metrics(facts_data)
        
        if metrics:
            company_data[ticker] = {
                'latest_10k_date': latest_10k_date,
                'metrics': metrics
            }
    
    # Save results
    with open('company_summary.json', 'w') as f:
        json.dump(company_data, f, indent=2)
    
    print("\nAnalysis Summary:")
    for ticker, data in company_data.items():
        print(f"\n{ticker}:")
        print(f"Latest 10-K Date: {data['latest_10k_date']}")
        if data['metrics']:
            for metric, value in data['metrics'].items():
                print(f"{metric}: {value['value']:,.2f} {value['unit']} ({value['date']})")

if __name__ == "__main__":
    main()