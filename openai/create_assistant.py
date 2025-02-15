import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Assistant prompt
prompt = """
You are an expert in market research and competitive analysis. Your task is to analyze a given list of public companies and provide insights into their market positioning.
Ensure responses are well-organized, concise, and actionable.
"""

def upload_file(file_path):
    """Uploads a file to OpenAI and returns the file ID."""
    response = openai.files.create(
        file=open(file_path, "rb"),
        purpose="assistants"
    )
    print('Uploaded File Response:', response)
    return response.id 

def create_vector_store(file_ids):
    """Creates a vector store using the uploaded file IDs."""
    response = openai.beta.vector_stores.create(
        name="Market Research Vector Store",
        file_ids=file_ids
    )
    print('Created Vector Store Response:', response)
    return response.id 

def create_assistant(vector_store_id):
    """Creates a new OpenAI assistant with the given vector store."""
    response = openai.beta.assistants.create(
        name="Market Research Assistant",
        instructions=prompt,
        model="gpt-3.5-turbo",
        tools=[{"type": "file_search"}],  
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}  
    )
    return response.id

def update_assistant(assistant_id, vector_store_id):
    """Updates an existing OpenAI assistant by adding a new vector store."""
    response = openai.beta.assistants.update(
        assistant_id=assistant_id,
        instructions=prompt,
        tools=[{"type": "file_search"}],  
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}  
    )
    return response.id

if __name__ == "__main__":
    # List of files to upload
    files = ["./company_summary.json", "./stock_data.json", "./yahoo_results.json"]
    
    # Upload files and get file IDs
    # file_ids = [upload_file(file) for file in files]
    # print("Uploaded File IDs:", file_ids)

    # # Create a vector store using the uploaded file IDs
    # vector_store_id = create_vector_store(file_ids)
    vector_store_id = "vs_67ae0b3184088191afb5637054e25714"
    print("Vector Store ID:", vector_store_id)

    # Fetch assistant ID from .env
    # assistant_id = os.getenv("ASSISTANT_ID")   

    # if assistant_id:
    #     updated_assistant_id = update_assistant(assistant_id, vector_store_id)
    #     print(f"PLACE THIS IN THE .ENV LIKE")
    #     print("ASSISTANT_ID=assistant id placeholder")
    #     print(f"Updated Assistant ID: {updated_assistant_id}")
    # else:
    new_assistant_id = create_assistant(vector_store_id)
    print(f"PLACE THIS IN THE .ENV LIKE")
    print("ASSISTANT_ID=assistant id placeholder")
    print(f"Created New Assistant ID: {new_assistant_id}")
# ASSISTANT_ID=asst_fGsb9TCoAZXfR7Dd4OEKzFNq