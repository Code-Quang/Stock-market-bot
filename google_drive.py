from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

# Define the scope
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def authenticate_drive():
    """Authenticate and return a Google Drive service instance"""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)

def upload_file(file_path, folder_id=None):
    """Upload a single file to Google Drive"""
    service = authenticate_drive()
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    file_metadata = {"name": os.path.basename(file_path)}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    print(f"Uploaded: {file_path} | File ID: {file.get('id')}")

def upload_multiple_files(file_paths, folder_id=None):
    """Upload multiple files to Google Drive"""
    for file_path in file_paths:
        upload_file(file_path, folder_id)

# List of files to upload
files = [
    "./output_pdfs/analyst_reports.pdf",
    "./output_pdfs/earnings_call.pdf",
    "./output_pdfs/web_scraped_data.pdf",
    "./output_pdfs/sec_financial_data.pdf",
    "./output_pdfs/yahoo_results.pdf",
    "./output_pdfs/company_summary.pdf",
    "./market_research.xlsx"
]

# Optional: Specify a Google Drive folder ID (leave None to upload to root)
folder_id = None  # Replace with actual folder ID if needed

# Call the function to upload all files
upload_multiple_files(files, folder_id)
