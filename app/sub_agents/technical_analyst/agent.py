
"""technical_analyst_agent for calculating technical indicators"""

from google.adk import Agent
from . import prompt
from . import tools

MODEL = "gemini-2.0-flash-001"

technical_analyst_agent = Agent(
    model=MODEL,
    name="technical_analyst_agent",
    instruction=prompt.TECHNICAL_ANALYST_PROMPT,
    output_key="technical_analysis_output",
    tools=[tools.get_technical_indicators],
)
