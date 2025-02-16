# test_env_load.py

from dotenv import load_dotenv
import os
import openai

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

print("API Key found:", "Yes" if api_key else "No")
if api_key:
    print("API Key starts with:", api_key[:7])  # Only show beginning to keep it secure
    
    # Test the API key
    try:
        client = openai.OpenAI(api_key=api_key)
        # Make a simple API call
        response = client.models.list()
        print("API Key is valid - successfully connected to OpenAI")
    except Exception as e:
        print("Error testing API key:", str(e))