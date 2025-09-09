import requests
import json
import os

API_BASE_URL = os.getenv("NTH_API_BASE_URL", "http://127.0.0.1:8002")
API_URL = f"{API_BASE_URL.rstrip('/')}\/search"

def search_nth_database(query: str) -> str:
    try:
        response = requests.post(API_URL, json={"query": query})
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"status": "error", "message": f"Failed to connect to NTH API: {e}"})
