"""Tool for Human-in-the-Loop Gating."""

from google.adk.tools import FunctionTool

def ask_user_permission(question: str) -> str:
    """
    Asks the user for permission to proceed with a sensitive action.
    This tool effectively pauses the agent's execution flow until the user responds.
    
    Args:
        question: The question to ask the user (e.g., "Do you want to generate the Strategic Blueprint?").
        
    Returns:
        The user's response (simulated or actual). 
        In the ADK context, calling this tool should be the LAST action of the turn.
    """
    # In a real agent loop, this might trigger a UI prompt.
    # For ADK, returning this string signals the Intent to the user.
    print(f"DEBUG: GATE TRIGGERED. Question: {question}")
    return f"GATE_PAUSE: {question}"

human_gate_tool = FunctionTool(func=ask_user_permission)





