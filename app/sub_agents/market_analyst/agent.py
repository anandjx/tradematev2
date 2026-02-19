"""market_analyst_agent for fetching market data"""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types
from . import prompt

MODEL = "gemini-2.5-flash"
MODEL1PRO = "gemini-3-pro-preview"
MODEL1FLASH = "gemini-3-flash-preview"

market_analyst_agent = LlmAgent(
    model=MODEL1PRO,
    name="market_analyst_agent",
    instruction=prompt.MARKET_ANALYST_PROMPT,
    tools=[google_search], # Pure Search Mode
    output_key="market_analyst_report",  # Auto-saves agent's text response to state
    
    )
