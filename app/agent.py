"""Financial coordinator: provide reasonable investment strategies."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.config import config

from . import prompt
from .sub_agents.technical_analyst import technical_analyst_agent
from .sub_agents.market_analyst import market_analyst_agent
from .sub_agents.market_analyst.tools import submit_market_report, search_ticker # Moved here for stability
from .sub_agents.quant_synthesis.tools import quant_synthesis_tool  # Stateless Function Tool
from .sub_agents.investment_consultant.tools import investment_consultant_tool # New Strategy Tool
# Import Oracle's TOOL directly, not the Agent wrapper
from .sub_agents.oracle_predictor.tools import clean_and_forecast
from .sub_agents.human_gate import human_gate_tool
from .sub_agents.report_generator.tools import equity_report_tool  # Equity Research Report


print(f"DEBUG: Initializing LlmAgent with name='{config.internal_agent_name}' (config.deployment_name='{config.deployment_name}')")

financial_coordinator = LlmAgent(
    name=config.deployment_name,  # Use deployment_name ("trademate") directly, not internal name ("agent_trademate")
    model=config.model,
    description=(
        "An intelligent multiagent system that guide users through a structured process to receive financial "
        "advice by orchestrating a series of expert subagents. help them "
        "analyze a market ticker, develop trading strategies, define "
        "execution plans, and evaluate the overall risk."
    ),
    instruction=prompt.FINANCIAL_COORDINATOR_PROMPT,
    output_key="financial_coordinator_output",
    tools=[        
        AgentTool(agent=market_analyst_agent),
        submit_market_report, # Coordinator handles submission now
        AgentTool(agent=technical_analyst_agent),
        quant_synthesis_tool,  # New Stateless Tool
        investment_consultant_tool, # New Strategy Tool
        clean_and_forecast,  # Direct FunctionTool, NOT wrapped in AgentTool
        human_gate_tool, # Gatekeeper
        equity_report_tool,  # Deterministic HTML Report Generator
        search_ticker,  # Ticker Verification (Moved to Coordinator)
    ],
)

root_agent = financial_coordinator