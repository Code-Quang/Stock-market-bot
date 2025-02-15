import openai
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Fetch assistant ID from .env or manually set it
ASSISTANT_ID = os.getenv("ASSISTANT_ID")  # Ensure this is set in your .env file

def create_thread():
    """Creates a new thread for conversation."""
    response = openai.beta.threads.create()
    return response.id

def send_message(thread_id, user_message):
    """Sends a user message to the assistant."""
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

def run_assistant(thread_id):
    """Runs the assistant on the given thread and waits for completion."""
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    print("\nAssistant is thinking...", end="", flush=True)

    # Wait for the assistant to complete processing
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == "completed":
            print("\r", end="")  # Clear the "thinking" message
            break
        print(".", end="", flush=True)  # Show dots while waiting
        time.sleep(2)  # Wait before checking again

def get_response(thread_id):
    """Retrieves the latest assistant response from the thread."""
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    # print('messages:',messages)
    for message in messages.data:  # Reverse to get the latest messages first
        if message.role == "assistant":
            text_response = message.content[0].text.value.strip()  # Extract and clean response
            return text_response if text_response else "I don't have an answer for that."

    return "I didn't get a response. Please try again."

if __name__ == "__main__":
    thread_id = create_thread()  # Create a new conversation thread
    print(f"Thread ID: {thread_id}")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat...")
            break
        
        send_message(thread_id, user_input)  # Send user input
        run_assistant(thread_id)  # Process input
        response = get_response(thread_id)  # Get response

        print(f"Assistant: {response}")
