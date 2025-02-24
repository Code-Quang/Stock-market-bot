import openai
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# File to store assistant ID
ASSISTANT_ID_FILE = "assistant_id.txt"

# Assistant prompt
prompt = """
You are an expert in market research and competitive analysis. Your task is to analyze a given list of public companies and provide insights into their market positioning.
Ensure responses are well-organized, concise, and actionable.
"""

def upload_file(file_path):
    """Uploads a file to OpenAI and returns the file ID."""
    try:
        response = openai.files.create(
            file=open(file_path, "rb"),
            purpose="assistants"
        )
        print('Uploaded File Response:', response)
        return response.id
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")
        return None

def create_vector_store(file_ids):
    """Creates a vector store using the uploaded file IDs."""
    try:
        response = openai.beta.vector_stores.create(
            name="Market Research Vector Store",
            file_ids=file_ids
        )
        print('Created Vector Store Response:', response)
        return response.id
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

def create_assistant(vector_store_id):
    """Creates a new OpenAI assistant with the given vector store."""
    try:
        response = openai.beta.assistants.create(
            name="Market Research Assistant",
            instructions=prompt,
            model="gpt-3.5-turbo",
            tools=[{"type": "file_search"}],  
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}  
        )
        return response.id
    except Exception as e:
        print(f"Error creating assistant: {e}")
        return None

def update_assistant(assistant_id, vector_store_id):
    """Updates an existing OpenAI assistant by adding a new vector store."""
    try:
        response = openai.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=prompt,
            tools=[{"type": "file_search"}],  
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}  
        )
        return response.id
    except Exception as e:
        print(f"Error updating assistant: {e}")
        return None

def read_assistant_id():
    """Reads the assistant ID from a text file."""
    if os.path.exists(ASSISTANT_ID_FILE):
        with open(ASSISTANT_ID_FILE, "r") as f:
            assistant_id = f.read().strip()
            return assistant_id if assistant_id else None
    return None

def write_assistant_id(assistant_id):
    """Writes the assistant ID to a text file."""
    with open(ASSISTANT_ID_FILE, "w") as f:
        f.write(assistant_id)

if __name__ == "__main__":
    # List of files to upload
    files = ["./company_summary.json", "./stock_data.json", "./yahoo_results.json"]
    
    # Upload files and get file IDs
    # this did DOUBLE uploads:  file_ids = [upload_file(file) for file in files if upload_file(file) is not None]
    file_ids = [id for file in files if (id := upload_file(file)) is not None]

    if not file_ids:
        print("No files were uploaded. Exiting...")
        exit(1)

    # Create a vector store using the uploaded file IDs
    vector_store_id = create_vector_store(file_ids)
    
    if not vector_store_id:
        print("Failed to create vector store. Exiting...")
        exit(1)

    print("Vector Store ID:", vector_store_id)

    # Read assistant ID from file
    assistant_id = read_assistant_id()

    if assistant_id:
        updated_assistant_id = update_assistant(assistant_id, vector_store_id)
        if updated_assistant_id:
            print(f"Updated Assistant ID: {updated_assistant_id}")
        else:
            print("Failed to update assistant.")
    else:
        new_assistant_id = create_assistant(vector_store_id)
        if new_assistant_id:
            write_assistant_id(new_assistant_id)
            print(f"Created New Assistant ID: {new_assistant_id}")
        else:
            print("Failed to create a new assistant.")
