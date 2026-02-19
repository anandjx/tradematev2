"""Oracle Predictor Agent for Quantitative Forecasting."""

from google.adk.agents import Agent, LlmAgent
from google.adk.tools import FunctionTool
from . import prompt
from . import tools

MODEL0 = "gemini-2.0-flash-001"
MODEL = "gemini-2.5-flash"
MODEL1PRO = "gemini-3-pro-preview"
MODEL1FLASH = "gemini-3-flash-preview"

oracle_predictor_agent = LlmAgent(
    model=MODEL,
    name="oracle_predictor_agent",
    instruction=prompt.ORACLE_PREDICTOR_PROMPT,
    description="A specialist agent that performs quantitative price forecasting (14-30 days) using TimesFM 2.5 and Wavelet Denoising. Use this for all 'Forecast', 'Target', or 'Prediction' requests.",
    tools=[tools.clean_and_forecast],
)
