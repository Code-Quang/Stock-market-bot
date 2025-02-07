import requests
import json
import time
import pandas as pd
from datetime import datetime
import re
from typing import Dict, List, Any

class SECDataExtractor:
    def __init__(self, user_agent: str = 'Company Name (email@domain.com)'):
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }
    
    def get_taxonomy(self, cik: str) -> List[str]:
        """Get all available GAAP concepts for a company"""
        cik_padded = cik.zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
        
        try:
            time.sleep(0.1)  
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            concepts = []
            if 'facts' in data and 'us-gaap' in data['facts']:
                concepts = list(data['facts']['us-gaap'].keys())
            
            return concepts
        except Exception as e:
            print(f"Error fetching taxonomy: {e}")
            return []

    def get_concept_data(self, cik: str, concept: str) -> Dict:
        """Fetch data for a single concept"""
        cik_padded = cik.zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik_padded}/us-gaap/{concept}.json"
        
        try:
            time.sleep(0.1)  # SEC rate limit compliance
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching concept {concept}: {e}")
            return {}

    def process_concept_data(self, data: Dict, concept: str) -> List[Dict]:
        """Process raw concept data into structured format"""
        processed_data = []
        
        if 'units' in data:
            for unit_type, values in data['units'].items():
                for value in values:
                    entry = {
                        'concept': concept,
                        'unit': unit_type,
                        'value': value.get('val'),
                        'end_date': value.get('end'),
                        'start_date': value.get('start'),
                        'filed_date': value.get('filed'),
                        'frame': value.get('frame'),
                        'form': value.get('form'),
                        'accn': value.get('accn')
                    }
                    processed_data.append(entry)
        
        return processed_data

def extract_cik_from_url(url: str) -> str:
    """Extract CIK from SEC URL"""
    pattern = r'/edgar/data/(\d+)/'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def main():
    extractor = SECDataExtractor()

    try:
        df = pd.read_csv('10k_links.csv', header=None, names=['ticker', 'url'])
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    

    all_data = {}
    processed_ciks = set()
    
    for _, row in df.iterrows():
        url = row['url']
        ticker = row['ticker']
        cik = extract_cik_from_url(url)
        
        if cik is None or cik in processed_ciks:
            continue
            
        print(f"Processing {ticker} (CIK: {cik})...")
        
        
        concepts = extractor.get_taxonomy(cik)
        print(f"Found {len(concepts)} concepts")
        
        company_data = []
        
        for concept in concepts:
            print(f"Fetching {concept}...")
            concept_data = extractor.get_concept_data(cik, concept)
            processed_data = extractor.process_concept_data(concept_data, concept)
            company_data.extend(processed_data)
        
        
        all_data[cik] = {
            'ticker': ticker,
            'data': company_data
        }
        
        processed_ciks.add(cik)
    
    
    output_file = 'sec_financial_data.json'
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\nData saved to {output_file}")
     
    print("\nSummary:")
    for cik, company_data in all_data.items():
        ticker = company_data['ticker']
        num_records = len(company_data['data'])
        num_concepts = len(set(d['concept'] for d in company_data['data']))
        print(f"{ticker} (CIK: {cik}): {num_records} records across {num_concepts} concepts")

if __name__ == "__main__":
    main()