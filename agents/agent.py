import requests

url = "http://localhost:8000/apps/agentic_system_app/users/test_user_01/sessions/session_01/run"

payload = {
    "appName": "agentic_system_app",
    "userId": "test_user_01",
    "sessionId": "session_01",
    "newMessage": {
        "role": "user",
        "parts": [
            {
                "text": "What were the key findings from the 2024 annual client report, and how do they compare to the tax implications outlined in document XYZ?"
            }
        ]
    },
    "streaming": False
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print("Status:", response.status_code)
print("Response:", response.json())
