# TradeMate Frontend (Ag-UI)

This is the Next.js frontend for TradeMate, integrated with CopilotKit.

## Prerequisites

1.  Backend dependencies installed in root `trademate` environment.
2.  Frontend dependencies installed (`npm install` done).

## Running the Application

You need two terminals.

### Terminal 1: Backend (FastAPI Agent Wrapper)

Navigate to the `trademate` root and run:

```bash
# Ensure your python environment is active
python app/frontend/backend/main.py
```

This starts the Agent API at `http://localhost:8000`.

### Terminal 2: Frontend (Next.js)

Navigate to `app/frontend` and run:

```bash
cd app/frontend
npm run dev
```

This starts the UI at `http://localhost:3000`.

## Architecture

*   **Frontend**: Next.js 14 (App Router) + CopilotKit
*   **Backend**: FastAPI Wrapper -> Google ADK Agent (`root_agent`)
*   **Communication**: Frontend calls `http://localhost:8000/copilotkit/chat`.
