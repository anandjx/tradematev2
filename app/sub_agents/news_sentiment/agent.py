from google.adk.agents import LlmAgent
from google.adk.tools import google_search
import google.genai.types as genai_types
from . import prompt

# Define the specialized agent
news_sentiment_agent = LlmAgent(
    name="news_sentiment_agent",
    instruction=prompt.NEWS_SENTIMENT_PROMPT,
    tools=[google_search],  # Uses search to read news
    model="gemini-2.0-flash" 
)
