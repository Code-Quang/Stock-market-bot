import csv
import re
import os
import time
import random
import pandas as pd
from openai import OpenAI
from openpyxl.styles import PatternFill

# Constants
ASSISTANT_ID_FILE = "assistant_id.txt"
RATE_LIMIT_DELAY = 10  # Start with 10 seconds (exponential backoff increases this)
MAX_RETRIES = 5  # Maximum retries per request
CHECK_INTERVAL = 5  # Time in seconds to check API status
TIMEOUT = 300  # Max wait time (5 minutes)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def read_companies(filename):
    """Reads companies and their tickers from a CSV file."""
    companies, tickers = [], []
    try:
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                for entry in row:
                    match = re.match(r"(.+?)\s\((\w+)\)", entry.strip())
                    if match:
                        companies.append(match.group(1))
                        tickers.append(match.group(2))
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return companies, tickers

def read_assistant_id():
    """Reads the assistant ID from a text file."""
    if os.path.exists(ASSISTANT_ID_FILE):
        with open(ASSISTANT_ID_FILE, "r") as f:
            return f.read().strip() or None
    return None

# def generate_questions():
#     """Generates questions based on Excel headers."""
#     return {
#         "DESCRIPTION": "Analyze {company} and provide a detailed description of their business.",
#         "PRODUCTS AND SERVICES": "List and describe the main products and services offered by {company}.",
#         "KEY MARKET 1": "What is {company}'s primary target market or industry vertical?",
#         "ESTIMATED MARKET SHARE TODAY": "What is {company}'s current estimated market share percentage?",
#         "SIC CODE": "What is the most appropriate SIC code for {company}?"
#     }



def generate_questions():
    """Generates questions based on the Excel headers."""
    return {
        "DESCRIPTION": "Analyze {company} and provide a detailed description of their business.",
        "PRODUCTS AND SERVICES": "List and describe the main products and services offered by {company}.",
        "KEY MARKET 1": "What is {company}'s primary target market or industry vertical?",
        "KEY MARKET 2": "What is {company}'s secondary target market?",
        "KEY MARKET 3": "What is {company}'s tertiary target market?",
        "KEY MARKET 4": "What other significant markets does {company} serve?",
        "KEY MARKET SIZE 1": "What is the total addressable market size (in USD) for {company}'s primary market?",
        "KEY MARKET SIZE 2": "What is the total addressable market size (in USD) for {company}'s secondary market?",
        "KEY MARKET SIZE 3": "What is the total addressable market size (in USD) for {company}'s tertiary market?",
        "KEY MARKET SIZE 4": "What is the total addressable market size (in USD) for {company}'s other significant markets?",
        "KEY MARKET GROWTH 1": "What is the projected 5-year CAGR for {company}'s primary market?",
        "KEY MARKET GROWTH 2": "What is the projected 5-year CAGR for {company}'s secondary market?",
        "KEY MARKET GROWTH 3": "What is the projected 5-year CAGR for {company}'s tertiary market?",
        "KEY MARKET GROWTH 4": "What is the projected 5-year CAGR for {company}'s other markets?",
        "COMPETITIVE STRENGTHS AND WEAKNESSES": "Analyze {company}'s competitive strengths and weaknesses in their market.",
        "ESTIMATED MARKET SHARE TODAY": "What is {company}'s current estimated market share percentage in their primary market?",
        "ESTIMATED MARKET SHARE FORECAST (5 YR)": "What is {company}'s projected market share percentage in 5 years?",
        "RELATIVE COMPETITIVE RANKING (NUMBER)": "What is {company}'s competitive ranking among peers (provide a number)?",
        "RELATIVE COMPETITIVE RANKING (EXPLANATION)": "Explain {company}'s competitive position relative to key competitors.",
        "CLASS": "What is {company}'s primary industry classification?",
        "SUB CLASS": "What is {company}'s industry sub-classification?",
        "SUB SUB CLASS": "What is {company}'s detailed industry category?",
        "SIC CODE": "What is the most appropriate SIC code for {company}?",
        "NAICS CODE": "What is the most appropriate NAICS code for {company}?",
        "LINKEDIN CLASSIFICATION": "How is {company}'s industry classified on LinkedIn?",
        "OTHER TAXONOMIES": "What other relevant industry classifications apply to {company}?"
    }

def query_assistant(assistant_id, question):
    """Queries OpenAI Assistant with rate limit handling and retries."""
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            time.sleep(random.uniform(2, 5))  # Random delay to avoid hitting rate limits
            
            print("Creating a new thread...")
            thread = client.beta.threads.create()
            print(f"Thread ID: {thread.id}")

            # Add the question
            print("Sending question to the assistant...")
            client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=question
            )

            # Run the assistant
            print("Running assistant...")
            run = client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=assistant_id
            )

            # Wait for completion with timeout
            start_time = time.time()
            while True:
                time.sleep(CHECK_INTERVAL)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                print(f"Checking status: {run.status}")

                if run.status == "completed":
                    break  # Exit loop if done

                if run.status == "failed":
                    print(f"Run failed: {run}")
                    return "ERROR: Run failed"

                if time.time() - start_time > TIMEOUT:
                    print("Timeout reached! Skipping this request...")
                    return "ERROR: Timeout"

            # Retrieve response
            print("Retrieving response...")
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            if not messages.data:
                print("No messages found in thread!")
                return "ERROR: No response received"

            answer = messages.data[0].content[0].text.value
            print(f"Received answer: {answer[:50]}...")  # Print only the first 50 chars
            return answer

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            time.sleep(RATE_LIMIT_DELAY * (2 ** attempt))  # Exponential backoff

    print(f"Skipping question due to repeated failures: {question}")
    return "ERROR: API failed"

def write_to_excel(data, output_file):
    """Writes the collected data to an Excel file."""
    try:
        df = pd.DataFrame(data)
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Market Research')

            # Apply header styling
            workbook = writer.book
            worksheet = workbook.active
            header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
            for cell in worksheet[1]:
                cell.fill = header_fill

        print(f"Successfully wrote data to {output_file}")
    except Exception as e:
        print(f"Error writing to Excel: {e}")

def main():
    companies, tickers = read_companies("companies.csv")
    if not companies:
        print("No companies found.")
        return

    assistant_id = read_assistant_id()
    if not assistant_id:
        print("No assistant ID found.")
        return

    questions = generate_questions()
    data = []

    for company, ticker in zip(companies, tickers):
        print(f"Processing company: {company} ({ticker})")
        company_data = {"COMPANY": company, "TICKER": ticker}

        for key, question_template in questions.items():
            question = question_template.format(company=company)
            print(f"Asking: {question}")
            answer = query_assistant(assistant_id, question)
            company_data[key] = answer

        data.append(company_data)
        print(f"Finished processing {company}")

        time.sleep(random.uniform(5, 10))  # Add a delay to prevent hitting rate limits

    write_to_excel(data, "market_research.xlsx")

if __name__ == "__main__":
    main()


# MeridianLink Inc. (MLNK),PagerDuty Inc. (PD),Amplitude Inc. (AMPL),CompoSecure Inc. (CMPO),Weave Communications Inc. (WEAV),VNET Group Inc. (VNET),8x8 Inc. (EGHT)