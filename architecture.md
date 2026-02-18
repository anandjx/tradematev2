# TradeMate System Architecture

TradeMate is an **Agentic Financial Intelligence Platform** that orchestrates a team of specialized AI sub-agents to provide institutional-grade market analysis, quantitative forecasting, and strategic investment blueprints.

## 1. High-Level Architecture

The system follows a **Hybrid Agentic Architecture**, combining a stateful Orchestrator (ADK Agent) with stateless expert function tools, wrapped in a FastAPI gateway for frontend communication via the AG-UI protocol.

```mermaid
graph TD
    User([User]) <--> Frontend[Next.js Frontend\n(AG-UI Client)]
    Frontend <--> API[FastAPI Gateway\n(ag_ui_adk Middleware)]
    API <--> Coordinator[Financial Coordinator Agent\n(Googe ADK / Vertex AI)]
    
    subgraph "Agent War Room (Execution Layer)"
        Coordinator --> Market[Market Analyst Agent]
        Coordinator --> Technical[Technical Analyst Agent]
        Coordinator --> Oracle[Oracle Predictor Tool\n(BigQuery + TimesFM 2.5)]
        Coordinator --> Quant[Quant Synthesis Tool\n(Gemini 1.5 Pro)]
        Coordinator --> Strategy[Investment Consultant Tool\n(Gemini 1.5 Pro)]
        Coordinator --> Gate[Human Gate Tool]
    end

    subgraph "Data & Infrastructure"
        Market <--> WebSearch[Google Search / News API]
        Technical <--> YF[YFinance API]
        Oracle <--> BigQuery[Google BigQuery\n(Time Series Store)]
        Oracle <--> Vertex[Vertex AI\n(Forecasting Models)]
    end
```

---

## 2. Core Components

### 2.1 Backend (`app/`)
* **Framework**: Google ADK (Agent Development Kit) & Python 3.11+
* **Coordinator Agent** (`app/agent.py`):
    * Acts as the "Manager" (Persona: Mark Hanna).
    * Routes user intent to specific sub-agents.
    * Manages conversation state and context.
* **Sub-Agents & Tools**:
    1. **Market Analyst**: Conducts deep fundamental research and sentiment analysis.
    2. **Technical Analyst**: Computes RSI, MACD, Bollinger Bands, and trend lines.
    3. **Oracle Predictor**: Retrieves historical data, denoises it (Hampel/Wavelet), and runs **TimesFM 2.5** forecasts via BigQuery.
    4. **Quant Synthesis**: Synthesizes narrative, technicals, and forecasts into a unified "Buy-Side" memo (Stateless Tool).
    5. **Investment Consultant**: Generates conditional execution strategies (Entry, Stop-Loss, Take-Profit) (Stateless Tool).
    6. **Human Gate**: Pauses execution to request user confirmation before generating strategies.

### 2.2 API Layer (`app/frontend/backend/main.py`)
* **FastAPI**: Serves the agent logic.
* **Middleware**: `ag_ui_adk` connects the ADK agent to the Frontend's `CopilotKit`, enabling streaming responses and state synchronization.

### 2.3 Frontend (`app/frontend/`)
* **Framework**: Next.js 14 (App Router) & React.
* **State Management**: `CopilotKit` (`useCoAgent`, `useCoAgentStateRender`).
* **UI Components**:
    * **Glassmorphic Design System**: Custom CSS for premium financial aesthetic.
    * **Interactive Cards**:
        * `MarketAnalysisCard`: Sentiment & Fundamental data.
        * `TechnicalAnalysisCard`: Live indicators & charts.
        * `OracleForecastCard`: 30-day price path visualization with volatility ribbons.
        * `QuantSynthesisCard`: AI-generated synthesis memo.
        * `StrategicBlueprintCard`: Actionable trade setup.

---

## 3. Data Flow & Event Pipeline

The system uses a strict **SOP (Standard Operating Procedure)** defined in the `FINANCIAL_COORDINATOR_PROMPT`.

1.  **Trigger**: User inputs a Ticker (e.g., "AAPL").
2.  **Phase 1: Intelligence Gathering**
    *   **Market Scan**: Coordinator calls `market_analyst` -> Returns Sentiment Cloud & News.
    *   **Technical Check**: Coordinator calls `technical_analyst` -> Returns Indicators.
3.  **Phase 2: Forecasting**
    *   **Oracle Prediction**: Coordinator calls `oracle_predictor` ->
        *   Uploads Data to BigQuery.
        *   Runs `AI.FORECAST` (TimesFM 2.5).
        *   Returns 30-day path + Confidence Intervals.
4.  **Phase 3: Synthesis**
    *   **Quant Synthesis**: Coordinator calls `quant_synthesis` -> Fuses Phase 1 & 2 data into a Summary.
5.  **Phase 4: Strategy (Gated)**
    *   **Human Gate**: Coordinator pauses and asks: *"Shall I generate the blueprint?"*
    *   **User Action**: User approves (Click or Text).
    *   **Strategy Generation**: Coordinator calls `investment_consultant` -> Returns Execution Plan.

---

## 4. Key Technical Decisions

*   **Stateless Tools for High-Reasoning Tasks**: The `Quant Synthesis` and `Investment Consultant` steps use `FunctionTool` wrapping direct LLM calls (Gemini 1.5 Pro). This prevents context pollution and ensures each step uses fresh, specific reasoning.
*   **BigQuery Integration**: Heavy time-series lifting is offloaded to BigQuery, utilizing its scalable compute for signal processing and forecasting.
*   **AG-UI Protocol**: Enables a "Shared State" architecture where the Backend pushes JSON state updates (e.g., `{ pipeline_stage: "market_scan" }`), and the Frontend reactively renders the appropriate UI card.

## 5. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **LLM** | **Gemini 2.0 Flash / 1.5 Pro** | Core Reasoning & Generative Tasks |
| **Forecasting** | **TimesFM 2.5** (Vertex AI) | Time-series prediction |
| **Agent Fx** | **Google ADK** | Agent orchestration & Tool management |
| **Backend** | **FastAPI + Python** | API Gateway & Business Logic |
| **Frontend** | **Next.js + TypeScript** | User Interface |
| **Styling** | **TailwindCSS + Custom CSS** | "Glassmorphism" Design System |
| **Database** | **Google BigQuery** | Transient Time-Series Storage |
