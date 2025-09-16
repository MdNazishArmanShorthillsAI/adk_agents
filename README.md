
## Running with API Key Authentication

This project supports API-level authentication using a shared secret (API key) via FastAPI middleware.

### 1. Set environment variables

Create a `.env` file or export the following variables:

```
ADK_API_KEY=your-secret-api-key
SESSION_DB_URL=postgresql+psycopg2://user:password@localhost:5432/agentic_ai
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Start the server

```
uvicorn serve_api_key:app --host 0.0.0.0 --port 8010
```

### 4. Test the API

Use curl or httpie to make authenticated requests:

```
curl -i http://127.0.0.1:8010/run \
  -H "x-api-key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"appName":"agents","userId":"user","sessionId":"...","newMessage":{"role":"user","parts":[{"text":"hello"}]}}'
```

If the API key is missing or incorrect, you will receive a 401 Unauthorized error. 