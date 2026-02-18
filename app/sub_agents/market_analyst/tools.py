
import yfinance as yf
import requests
import json
from google.adk.tools import FunctionTool, ToolContext

def search_ticker_func(query: str, tool_context: ToolContext) -> str:
    """
    Searches for a stock ticker symbol by company name.
    
    Args:
        query: The company name or search term (e.g., "Apple", "Tesla").
        
    Returns:
        A list of potential matches with symbols and names, or a message if none found.
    """
    # Emit state for frontend
    tool_context.state["pipeline_stage"] = "market_scan"
    tool_context.state["stages_completed"] = tool_context.state.get("stages_completed", [])
    
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": query, "quotes_count": 5, "country": "United States"}
        headers = {"User-Agent": "Mozilla/5.0"}

        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        quotes = data.get("quotes", [])
        
        results = []
        for q in quotes:
            symbol = q.get("symbol")
            shortname = q.get("shortname")
            exch = q.get("exchange")
            if symbol and shortname:
                results.append(f"{symbol} ({shortname} - {exch})")
                
        if not results:
            return f"No tickers found for '{query}'. Please verify the name."
            
        return "Found Matches:\n" + "\n".join(results)
    except Exception as e:
        return f"Error searching for ticker '{query}': {str(e)}"

def get_market_data_func(ticker: str, tool_context: ToolContext) -> str:
    """
    Fetches real-time market data and fundamental info for a given ticker.
    
    Args:
        ticker: The stock ticker symbol.
        
    Returns:
        JSON string with current price, volume, market cap, sector, and key ratios.
    """
    # Emit state for frontend
    tool_context.state["pipeline_stage"] = "market_scan"
    tool_context.state["target_ticker"] = ticker
    
    # --- VISIBLE LOGGING FOR USER ---
    print(f"\n{'='*50}")
    print(f"🚀 USER REQUESTED TICKER: {ticker}")
    print(f"{'='*50}\n")
    # --------------------------------

    stages = tool_context.state.get("stages_completed", [])
    if "market_scan" not in stages:
        stages.append("market_scan")
    tool_context.state["stages_completed"] = stages
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # safely get keys
        data = {
            "ticker": ticker,
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "beta": info.get("beta"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "company_summary": info.get("longBusinessSummary")
        }
        
        # Store market analysis in state for frontend
        tool_context.state["market_analysis"] = {
            "sentiment": "Neutral",  # Will be determined by agent
            "key_drivers": [info.get("sector", "Unknown Sector")],
            "sector_performance": info.get("industry", "Unknown Industry"),
            "current_price": data["current_price"],
            "market_cap": data["market_cap"],
        }
        
        return str(data)
    except Exception as e:
        return f"Error fetching market data for {ticker}: {str(e)}"

# ... (previous code)

def submit_market_report_func(report_content: str, tool_context: ToolContext) -> str:
    """
    Publishes the final Market Analysis Report to the main dashboard.
    
    Args:
        report_content: The full markdown text of the market analysis report.
        
    Returns:
        Confirmation string.
    """
    # Emit state for frontend
    # We preserve existing market_analysis data (prices, etc) and add the report
    existing_data = tool_context.state.get("market_analysis", {})
    if not isinstance(existing_data, dict):
        existing_data = {}
        
    existing_data["report"] = report_content
    # Also parse out a quick summary/sentiment if possible, but the full report is key
    tool_context.state["market_analysis"] = existing_data
    
    # Also update pipeline stage if needed, though usually we stay in market_scan until done
    tool_context.state["stages_completed"] = list(set(tool_context.state.get("stages_completed", []) + ["market_scan"]))
    
    return "Market Report Published to Dashboard Successfully."

# Create FunctionTool instances
search_ticker = FunctionTool(func=search_ticker_func)
get_market_data = FunctionTool(func=get_market_data_func)
submit_market_report = FunctionTool(func=submit_market_report_func)


