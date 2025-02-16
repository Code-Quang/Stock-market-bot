from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")