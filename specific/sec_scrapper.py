import requests
import json
import time
import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any


class CompanyAnalyzer:
    def __init__(self, user_agent: str = 'Company Name (email@domain.com)'):
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json',
            'Host': 'data.sec.gov'
        }
    
    def _format_cik(self, cik: str) -> str:
        return str(int(cik)).zfill(10)

    def fetch_json(self, url: str) -> Dict:
        try:
            print(f"Fetching: {url}")
            time.sleep(0.1)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return {}

    def get_company_facts(self, cik: str) -> Dict:
        cik_padded = self._format_cik(cik)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
        return self.fetch_json(url)

    def get_company_info(self, cik: str) -> Dict:
        cik_padded = self._format_cik(cik)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        return self.fetch_json(url)

    def extract_latest_metrics(self, facts_data: Dict) -> Dict:
        if not facts_data or 'facts' not in facts_data:
            return {"Revenue": "Not Available", "Net Income": "Not Available"}

        metrics_to_extract = {
            'Revenues': 'Revenue',
            'NetIncomeLoss': 'Net Income',
            'OperatingIncomeLoss': 'Operating Income',
            'Assets': 'Total Assets',
            'Liabilities': 'Total Liabilities',
            'StockholdersEquity': 'Stockholders Equity',
            'EarningsPerShareBasic': 'EPS',
            'GrossProfit': 'Gross Profit',
            'CashAndCashEquivalentsAtCarryingValue': 'Cash & Cash Equivalents'
        }

        extracted_metrics = {}
        us_gaap_data = facts_data.get('facts', {}).get('us-gaap', {})
        dei_data = facts_data.get('facts', {}).get('dei', {})  # Alternative source

        for metric_key, metric_name in metrics_to_extract.items():
            values = us_gaap_data.get(metric_key, {}).get('units', {}).get('USD', []) or \
                     dei_data.get(metric_key, {}).get('units', {}).get('USD', [])

            if values:
                latest_value = max(values, key=lambda x: x.get('end', ''))
                extracted_metrics[metric_name] = latest_value.get('val', "Not Available")
            else:
                extracted_metrics[metric_name] = "Not Available"

        return extracted_metrics

    def get_latest_10k_text(self, cik: str) -> Dict:
        company_info = self.get_company_info(cik)
        if not company_info:
            return {"Business Description": "Not Available", "Risk Factors": "Not Available"}

        latest_10k_url = None
        if 'filings' in company_info and 'recent' in company_info['filings']:
            for idx, form in enumerate(company_info['filings']['recent']['form']):
                if form == '10-K':
                    latest_10k_url = f"https://www.sec.gov{company_info['filings']['recent']['primaryDocument'][idx]}"
                    break

        if not latest_10k_url:
            return {"Business Description": "Not Available", "Risk Factors": "Not Available"}

        try:
            print(f"Fetching latest 10-K: {latest_10k_url}")
            response = requests.get(latest_10k_url, headers=self.headers)
            response.raise_for_status()
            text = response.text

            business_desc = re.search(r'ITEM\s*1\.\s*BUSINESS(.*?)(ITEM\s*1A\.\s*RISK\s*FACTORS|ITEM\s*2\.)', text, re.S)
            risk_factors = re.search(r'ITEM\s*1A\.\s*RISK\s*FACTORS(.*?)(ITEM\s*2\.)', text, re.S)

            return {
                "Business Description": business_desc.group(1).strip() if business_desc else "Not Available",
                "Risk Factors": risk_factors.group(1).strip() if risk_factors else "Not Available"
            }
        except Exception as e:
            print(f"Error fetching 10-K text: {e}")
            return {"Business Description": "Not Available", "Risk Factors": "Not Available"}

    def get_executive_info(self, company_info: Dict) -> Dict:
        if not company_info or 'officers' not in company_info:
            return {"Executives": "Not Available"}
        return {"Executives": company_info.get('officers', "Not Available")}

    def get_extra_info(self, company_info: Dict) -> Dict:
        """Extract additional details like SIC, Industry, Market Cap"""
        return {
            "SIC Code": company_info.get("sic", "Not Available"),
            "Industry": company_info.get("sicDescription", "Not Available"),
            "Market Cap": company_info.get("marketCap", "Not Available"),
            "Stock Price": company_info.get("stockPrice", "Not Available"),
         }


def main():
    analyzer = CompanyAnalyzer(user_agent='Your Company Name (your.email@domain.com)')

    try:
        df = pd.read_csv('10k_links.csv', header=None, names=['ticker', 'url'])
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    company_data = {}

    for _, row in df.iterrows():
        ticker = row['ticker']
        cik_match = re.search(r'/edgar/data/(\d+)/', row['url'])
        
        if not cik_match:
            print(f"Could not extract CIK for {ticker}, skipping...")
            continue
            
        cik = cik_match.group(1)
        print(f"\nProcessing {ticker} (CIK: {cik})...")

        facts_data = analyzer.get_company_facts(cik)
        # company_info = analyzer.get_company_info(cik)
        # business_data = analyzer.get_latest_10k_text(cik)
        # exec_data = analyzer.get_executive_info(company_info)
        # extra_data = analyzer.get_extra_info(company_info)

        metrics = analyzer.extract_latest_metrics(facts_data)

        company_data[ticker] = {
            'metrics': metrics
        }

    with open('company_summary.json', 'w') as f:
        json.dump(company_data, f, indent=2)

    print("✅ Analysis Complete! Data saved in company_summary.json")

if __name__ == "__main__":
    main()
