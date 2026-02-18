"""Tools for Investment Consultant Agent (Stateless)."""

import os
from google.adk.tools import FunctionTool, ToolContext
from google.genai import Client
from .prompt import INVESTMENT_CONSULTANT_PROMPT

def consult_on_strategy(ticker: str, quant_synthesis: str, horizon: str = "AUTO", tool_context: ToolContext = None) -> str:
    """
    Generates an elite-level execution strategy and risk analysis based on the Quantitative Synthesis.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL').
        quant_synthesis: The full text output from the Quantitative Synthesis Agent.
        horizon: The investment time horizon ('Short-Term', 'Medium-Term', 'Long-Term', or 'AUTO').
        
    Returns:
        A Markdown-formatted strategic execution plan.
    """
    # Emit state for frontend
    if tool_context:
        tool_context.state["pipeline_stage"] = "strategy_formulation"
        tool_context.state["target_ticker"] = ticker
        stages = tool_context.state.get("stages_completed", [])
        if "strategy_formulation" not in stages:
            stages.append("strategy_formulation")
        tool_context.state["stages_completed"] = stages
    
    # 1. Verification
    if not ticker or not quant_synthesis:
        return "ERROR: Missing Quant Synthesis. Cannot generate strategy."

    print(f"DEBUG: INVESTMENT CONSULTANT triggered for {ticker} (Horizon: {horizon})")
    
    # 2. Construct Prompt
    full_prompt = f"""
{INVESTMENT_CONSULTANT_PROMPT}

---

**INPUT CONTEXT:**

**1. TARGET ASSET:** {ticker}

**2. INVESTMENT HORIZON:** {horizon}

**3. QUANTITATIVE SYNTHESIS REPORT:**
{quant_synthesis}

---

**TASK:**
Generate the Strategic Blueprint for **{ticker}**.
"""

    try:
        # 3. Call Model (Stateless)
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = "global"
        model_id = "gemini-3-flash-preview"
        
        client = Client(project=project_id, location=location)
        
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt
        )
        
        result = response.text
        
        # Store strategic report in state for frontend
        if tool_context:
            tool_context.state["strategic_report"] = {
                "ticker": ticker,
                "overall_score": 75,  # Default, will be parsed from result
                "signal": "HOLD",  # Default
                "time_horizon": horizon if horizon != "AUTO" else "Medium-term",
                "narrative": result,  # Full Markdown from the Strategic Blueprint Agent
                "market_analysis": tool_context.state.get("market_analysis", {}),
                "technical_analysis": tool_context.state.get("technical_analysis", {}),
                "oracle_forecast": tool_context.state.get("oracle_forecast", {}),
                "strategic_plan": {
                    "action": "Review analysis",
                    "entry_price": 0,
                    "stop_loss": 0,
                    "take_profit": 0,
                    "risk_factors": [],
                },
            }
        
        return result

    except Exception as e:
        return f"ERROR in Investment Strategy Generation: {str(e)}"

# Create Tool
investment_consultant_tool = FunctionTool(func=consult_on_strategy)

