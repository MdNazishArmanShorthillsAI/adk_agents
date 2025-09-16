import os
import dotenv
from fastapi import FastAPI, Request, HTTPException
from google.adk.cli.fast_api import get_fast_api_app
from fastapi.responses import JSONResponse 


dotenv.load_dotenv()

API_KEY = os.environ.get("ADK_API_KEY")
SESSION_DB_URL = os.environ.get("SESSION_DB_URL")

if not API_KEY:
    raise RuntimeError("ADK_API_KEY must be set in the environment")
if not SESSION_DB_URL:
    raise RuntimeError("SESSION_DB_URL must be set in the environment")

# Create the ADK FastAPI app
adk_app: FastAPI = get_fast_api_app(
    agents_dir="./agents",
    session_service_uri=SESSION_DB_URL,
    allow_origins=[],  # Set CORS if needed
    web=True,
)

# Create a wrapper FastAPI app
app = FastAPI()

@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    # Allow unauthenticated access to /health endpoints
    if request.url.path.startswith("/health"):
        return await call_next(request)
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok", "message": "🚀 Server is running"})

# Mount the ADK app at root
app.mount("/", adk_app) 