"""FastAPI server wrapping ADK agent with AG-UI middleware.

This server provides an AG-UI compatible endpoint that wraps the existing
TradeMate agent without modifying any core agent files.
"""

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add app directory to path for imports
# Structure: app/frontend/backend/main.py
app_dir = Path(__file__).parent.parent.parent  # app/
project_root = app_dir.parent  # trademate/
sys.path.insert(0, str(project_root))

print(f"DEBUG: Starting main.py... App dir: {app_dir}")

# Load environment variables from app/.env
env_path = app_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("DEBUG: Loaded .env")
else:
    print("DEBUG: No .env found")

print("DEBUG: Importing ag_ui_adk...")
# Import AG-UI middleware (CopilotKit official package)
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
print("DEBUG: Imported ag_ui_adk successfully.")

print("DEBUG: Importing root_agent...")
# Import the EXISTING root_agent - no modifications needed
from app.agent import root_agent
print("DEBUG: Imported root_agent successfully.")

# Create AG-UI wrapper around the existing ADK agent
adk_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="trademate",  # Must match agent="trademate" in frontend
    user_id="demo_user",
    execution_timeout_seconds=300,  # 30 minutes for full pipeline
    tool_timeout_seconds=120,  # 10 minutes for individual tools
)

# Create FastAPI app
app = FastAPI(
    title="TradeMate API",
    description="AG-UI compatible API for TradeMate Financial Intelligence agent",
    version="1.0.0",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging removed to prevent Starlette RuntimeError with BaseHTTPMiddleware
# calling await request.body() inside middleware can break the request stream



@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "TradeMate Financial Coordinator"}


# --- Isolated Price Snapshot Endpoint (No Agent Involvement) ---
from app.sub_agents.technical_analyst.tools import get_price_timeseries_snapshot

@app.get("/api/price-snapshot")
async def price_snapshot(ticker: str, timeframe: str = "1D"):
    """Lightweight price chart data. No LLM, no agent, no pipeline."""
    result = get_price_timeseries_snapshot(ticker, timeframe)
    if "error" in result:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content=result)
    return result

 
# Add AG-UI endpoint at root path
# This handles all AG-UI protocol communication
add_adk_fastapi_endpoint(app, adk_agent, path="/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    # --- Windows fix: kill stale processes holding the port ---
    import subprocess, signal
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = int(parts[-1])
                if pid != os.getpid():
                    print(f"⚠️  Killing stale process on port {port} (PID {pid})")
                    os.kill(pid, signal.SIGTERM)
                    import time; time.sleep(1)
    except Exception:
        pass  # Best-effort cleanup

    print(f"Starting AG-UI server at http://0.0.0.0:{port}")
    print("Frontend should connect to this URL via /api/copilotkit proxy")
    uvicorn.run(app, host="0.0.0.0", port=port)
