from google.adk.agents import LlmAgent
from .prompt import QUANT_SYNTHESIS_PROMPT

# This agent is a pure reasoner; it doesn't need external tools, 
# just the context of the previous agents' outputs.

print("DEBUG: Loading Quant Synthesis Agent (Patched)")

quant_synthesis_agent = LlmAgent(
    name="quant_synthesis_agent",
    instruction=QUANT_SYNTHESIS_PROMPT,
    # model="gemini-2.0-flash-001" 
    model="gemini-3-flash-preview"
)

