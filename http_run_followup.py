#!/usr/bin/env python3
import argparse
import json
import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8010"
DEFAULT_APP_NAME = "agents"
DEFAULT_USER_ID = "user"
DEFAULT_SESSION_ID = "67f7b23c-2a78-4b30-a1d1-75645a9f7417"
DEFAULT_QUERY = "what is Maximum operating pressure for Series CQ2?"


def run_once(base_url: str, app_name: str, user_id: str, session_id: str, query: str) -> None:
    run_endpoint = f"{base_url}/run"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [
                {"text": query},
            ],
        },
        "streaming": False,
    }

    print(f"▶️  POST {run_endpoint} (session={session_id}) follow-up query")
    resp = requests.post(run_endpoint, headers=headers, json=payload)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ HTTP {resp.status_code}: {e}")
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)
        return

    try:
        data = resp.json()
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print(resp.text)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Call /run follow-up using the same session ID without re-upload")
    p.add_argument("--base_url", default=DEFAULT_BASE_URL)
    p.add_argument("--app", default=DEFAULT_APP_NAME)
    p.add_argument("--user", default=DEFAULT_USER_ID)
    p.add_argument("--session", default=DEFAULT_SESSION_ID)
    p.add_argument("--query", default=DEFAULT_QUERY)
    args = p.parse_args()

    run_once(
        base_url=args.base_url,
        app_name=args.app,
        user_id=args.user,
        session_id=args.session,
        query=args.query,
    ) 