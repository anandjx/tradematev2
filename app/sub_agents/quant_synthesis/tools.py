"""Tools for Quantitative Synthesis Agent (Stateless)."""

import os
from google.adk.tools import FunctionTool, ToolContext
from google.genai import Client
# We'll use the Gemini client directly to avoid Agent statefulness
# This ensures zero context leakage from previous turns.

from .prompt import QUANT_SYNTHESIS_PROMPT

def synthesize_reports(ticker: str, market_analysis: str, technical_analysis: str, oracle_forecast: str, tool_context: ToolContext) -> str:
    """
    Synthesizes the Market, Technical, and Oracle reports into a single high-signal Quantitative Synthesis.
    
    Args:
        ticker: The stock ticker symbol being analyzed (e.g., 'AAPL', 'NVDA', 'RELIANCE.NS').
        market_analysis: The full text report from the Market Analyst.
        technical_analysis: The full text report from the Technical Analyst.
        oracle_forecast: The full text/table output from the Oracle Predictor.
        
    Returns:
        A concise, buy-side grade Quantitative Synthesis string.
    """
    # Emit state for frontend
    tool_context.state["pipeline_stage"] = "quant_synthesis"
    tool_context.state["target_ticker"] = ticker
    stages = tool_context.state.get("stages_completed", [])
    if "quant_synthesis" not in stages:
        stages.append("quant_synthesis")
    tool_context.state["stages_completed"] = stages
    
    # 1. Verification of Inputs
    if not ticker or not market_analysis or not technical_analysis or not oracle_forecast:
        return "ERROR: Missing required reports for synthesis. Cannot proceed."
        
    print(f"DEBUG: STATLESS QUANT SYNTHESIS triggered for {ticker}")
    
    # 2. Construct the Prompt Context
    # We explicitly inject the reports into the prompt.
    full_prompt = f"""
{QUANT_SYNTHESIS_PROMPT}

---

**INPUT REPORTS FOR ANALYSIS:**

**1. TARGET ASSET:** {ticker}

**2. MARKET ANALYST REPORT:**
{market_analysis}

**3. TECHNICAL ANALYST REPORT:**
{technical_analysis}

**4. ORACLE PREDICTOR FORECAST:**
{oracle_forecast}

---

**TASK:**
Generate the Quantitative Synthesis for **{ticker}** based ONLY on the above reports.
Remember the Negative Constraints: Do not mention any other asset.
"""

    try:
        # 3. Call the Model Directly (Stateless)
        # Using the same configuration as the agent would have
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = "global" # Gemini 3 needs global
        model_id = "gemini-3-flash-preview" #"gemini-2.0-flash-001"
        
        client = Client(project=project_id, location=location)
        
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt
        )
        
        result = response.text
        
        # 4. Post-Process Verification (Safety Check)
        if "ANALYZING:" not in result:
             result = f"ANALYZING: {ticker}\n\n" + result
        
        # Store quant synthesis result in state for frontend
        tool_context.state["quant_synthesis"] = {
            "ticker": ticker,
            "synthesis_complete": True,
            "summary": result, # Full report, no truncation
        }
             
        return result

    except Exception as e:
        return f"ERROR in Quant Synthesis Generation: {str(e)}"

# Create the Tool
quant_synthesis_tool = FunctionTool(func=synthesize_reports)

