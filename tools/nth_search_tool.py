import requests
import json

API_URL = "http://127.0.0.1:8002/search"

def search_nth_database(query: str) -> str:
    try:
        response = requests.post(API_URL, json={"query": query})
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"status": "error", "message": f"Failed to connect to NTH API: {e}"})
