#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys
import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8010"
DEFAULT_APP_NAME = "agents"
DEFAULT_USER_ID = "user"
DEFAULT_SESSION_ID = "67f7b23c-2a78-4b30-a1d1-75645a9f7417"
DEFAULT_QUERY = "what about Contact Protection Boxes/CD-P11, CD-P12?"


def read_file_as_base64(path: str) -> tuple[str, str]:
    if not os.path.isfile(path):
        print(f"❌ File not found: {path}")
        sys.exit(1)
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return mime, b64


def run_once(base_url: str, app_name: str, user_id: str, session_id: str, query: str, doc_path: str) -> None:
    run_endpoint = f"{base_url}/run"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    mime_type, b64_data = read_file_as_base64(doc_path)

    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [
                {"text": query},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_data,
                    }
                },
            ],
        },
        "streaming": False,
    }

    print(f"▶️  POST {run_endpoint} (session={session_id}) with upload: {os.path.basename(doc_path)}")
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
    p = argparse.ArgumentParser(description="Call /run with a PDF upload using an existing session ID")
    p.add_argument("--base_url", default=DEFAULT_BASE_URL)
    p.add_argument("--app", default=DEFAULT_APP_NAME)
    p.add_argument("--user", default=DEFAULT_USER_ID)
    p.add_argument("--session", default=DEFAULT_SESSION_ID)
    p.add_argument("--query", default=DEFAULT_QUERY)
    p.add_argument("--file", required=True, help="Path to the PDF to upload")
    args = p.parse_args()

    run_once(
        base_url=args.base_url,
        app_name=args.app,
        user_id=args.user,
        session_id=args.session,
        query=args.query,
        doc_path=args.file,
    ) 