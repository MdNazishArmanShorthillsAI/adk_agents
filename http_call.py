import requests
import json
import uuid

# --- Configuration ---
# TODO: Replace with the actual URL of your FastAPI application
BASE_URL = "http://localhost:8000"

# TODO: Replace with your specific application, user, and session details
# These are example values.
APP_NAME = "agentic_system_app"
USER_ID = "test_user_01"
# A session ID is typically generated when a conversation starts.
# For this example, we'll generate a new one each time.
SESSION_ID = f"session_{uuid.uuid4()}"

# Your query to the agent
USER_QUERY = (
    "What were the key findings from the 2024 annual client report, "
    "and how do they compare to the tax implications outlined in document XYZ?"
)

# --- API Interaction ---

# The endpoint for the agent run command
run_endpoint = f"{BASE_URL}/run"

# Construct the request payload according to the OpenAPI schema
# This matches the 'AgentRunRequest' schema
payload = {
    "appName": APP_NAME,
    "userId": USER_ID,
    "sessionId": SESSION_ID,
    "newMessage": {
        "role": "user",
        "parts": [
            {
                "text": USER_QUERY
            }
        ]
    },
    "streaming": False # Set to True if you want to handle a streaming response
}

# Set the headers for the request
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

print(f"▶️  Sending query to agent at: {run_endpoint}")
print(f"▶️  Session ID: {SESSION_ID}")
print("-" * 20)

try:
    # Send the POST request to the agent. [1]
    # The `json` parameter in requests.post automatically handles
    # converting the dict to a JSON string and setting the Content-Type header. [2]
    response = requests.post(run_endpoint, headers=headers, json=payload)

    # Raise an exception for bad status codes (4xx or 5xx)
    response.raise_for_status()

    # Assuming the request was successful, process the JSON response
    print("✅ Success! Agent Response:")
    # The response is an array of 'Event-Output' objects. We'll print it prettily.
    response_data = response.json()
    print(json.dumps(response_data, indent=2))

except requests.exceptions.HTTPError as http_err:
    print(f"❌ HTTP error occurred: {http_err}")
    print(f"Response Body: {response.text}")
except requests.exceptions.RequestException as err:
    print(f"❌ An error occurred: {err}")
except json.JSONDecodeError:
    print("❌ Failed to decode JSON from response.")
    print(f"Response Text: {response.text}")