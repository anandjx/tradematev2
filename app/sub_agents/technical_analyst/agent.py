
"""technical_analyst_agent for calculating technical indicators"""

from google.adk import Agent
from . import prompt
from . import tools

MODEL = "gemini-2.5-flash"
MODELPRO = "gemini-2.5-pro"
MODEL1PRO = "gemini-3-pro-preview"
MODEL1FLASH = "gemini-3-flash-preview"

technical_analyst_agent = Agent(
    model=MODELPRO,
    name="technical_analyst_agent",
    instruction=prompt.TECHNICAL_ANALYST_PROMPT,
    output_key="technical_analysis_output",
    tools=[tools.get_technical_indicators],
)
