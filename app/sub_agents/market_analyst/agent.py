"""market_analyst_agent for fetching market data"""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from . import prompt

MODEL = "gemini-2.5-flash"

market_analyst_agent = LlmAgent(
    model=MODEL,
    name="market_analyst_agent",
    instruction=prompt.MARKET_ANALYST_PROMPT,
    tools=[google_search], # Pure Search Mode
    output_key="market_analyst_report",  # Auto-saves agent's text response to state
)
