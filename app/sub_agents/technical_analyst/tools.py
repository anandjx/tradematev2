
import os
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import io
from google.adk.tools import FunctionTool, ToolContext

# ------------------ Indicator Calculation Logic ------------------

def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd = ema_fast - ema_slow
    macd_signal = calculate_ema(macd, signal)
    return macd, macd_signal

def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2):
    sma = calculate_sma(series, period)
    rolling_std = series.rolling(period).std()
    upper = sma + std_dev * rolling_std
    lower = sma - std_dev * rolling_std
    return upper, lower

# ------------------ Data Fetching ------------------

def fetch_alpha_vantage(ticker: str) -> pd.DataFrame:
    """Fetch daily time series from Alpha Vantage."""
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("Alpha Vantage API key not found in environment variables.")

    # Sanitize ticker
    ticker = ticker.strip().upper()
    
    # AV Specific Logic for Indian Stocks
    # YFinance uses .NS, AV often handles just the symbol or specific prefixes
    # If it ends with .NS, AV might prefer just the symbol, or maybe we assume it finds it?
    # Actually, let's just pass it through first.
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={api_key}&datatype=csv"
    
    try:
        resp = requests.get(url, timeout=10) # Added timeout
    except Exception as e:
        raise ValueError(f"Alpha Vantage Connection Error: {str(e)}")
        
    if resp.status_code != 200:
        raise ValueError(f"Alpha Vantage HTTP Error {resp.status_code}: {resp.text}")
    
    if "Error Message" in resp.text:
        # Error likely due to invalid symbol.
        raise ValueError(f"Alpha Vantage API Error (Invalid Symbol?): {resp.text}")
        
    try:
        df = pd.read_csv(io.StringIO(resp.text))
    except Exception:
        raise ValueError("Alpha Vantage returned unparseable info (Rate Limit likely).")

    if df.empty or 'close' not in df.columns:
         if "Thank you" in resp.text or "call frequency" in resp.text: 
             raise ValueError("Alpha Vantage Rate Limit Reached.")
         raise ValueError(f"Alpha Vantage returned no data for {ticker}")

    # Standardize to Match YFinance Format
    df = df.rename(columns={
        'timestamp': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    return df

def download_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Download historical data, trying yfinance then Alpha Vantage."""
    errors = []
    
    # Clean ticker (standardize)
    original_ticker = ticker.strip().replace(" ", "").upper()
    
    # Strategy:
    # 1. Try Alpha Vantage with Original
    # 2. Try YFinance with Original
    # 3. IF Indian (.NS), try removing suffix for AV? Or try .BO for YF?
    
    # --- ATTEMPT 1: Alpha Vantage (Primary) ---
    try:
        # For AV, if it's .NS, maybe just try the root symbol?
        # But wait, AV supports global?
        # Let's try explicit mapping if .NS is present
        av_ticker = original_ticker
        # if av_ticker.endswith(".NS"): av_ticker = av_ticker.replace(".NS", "") # Optional heuristic
        
        data = fetch_alpha_vantage(av_ticker)
        if not data.empty:
            return data
    except Exception as e:
        errors.append(f"Alpha Vantage ({original_ticker}): {str(e)}")

    # --- ATTEMPT 2: Yahoo Finance (Fallback) ---
    try:
        data = yf.download(original_ticker, period=period, auto_adjust=True, progress=False)
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        if not data.empty and 'Close' in data.columns and not data['Close'].isna().all():
            return data
        else:
             errors.append(f"YFinance ({original_ticker}): No data/Delisted.")
    except Exception as e:
        errors.append(f"YFinance ({original_ticker}): {str(e)}")

    # --- ATTEMPT 3: Indian Fallback (If .NS failed, try .BO or vice versa) ---
    if ".NS" in original_ticker:
        alt_ticker = original_ticker.replace(".NS", ".BO")
        try:
             # Try YFinance with alternative
             data = yf.download(alt_ticker, period=period, auto_adjust=True, progress=False)
             if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
             if not data.empty and 'Close' in data.columns:
                 return data
             else:
                 errors.append(f"YFinance ({alt_ticker}): Also no data.")
        except Exception as e:
            errors.append(f"YFinance ({alt_ticker}): {str(e)}")

    # If all failed
    error_msg = " | ".join(errors)
    raise ValueError(
        f"DATA RETRIEVAL FAILURE for '{ticker}'.\n"
        f"Debug Trace: {error_msg}.\n"
        "Action: Verify ticker symbol (e.g., ADANI.NS vs ADANI.BO)."
    )

# ------------------ Tool Definition ------------------

def get_technical_indicators_func(ticker: str, tool_context: ToolContext) -> str:
    """
    Calculates technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands) for a given stock ticker.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'ADANIPOWER.NS').
        
    Returns:
        A JSON string containing the latest technical indicator values and a summary.
    """
    # Emit state for frontend
    tool_context.state["pipeline_stage"] = "technical_analysis"
    tool_context.state["target_ticker"] = ticker
    stages = tool_context.state.get("stages_completed", [])
    if "technical_analysis" not in stages:
        stages.append("technical_analysis")
    tool_context.state["stages_completed"] = stages
    
    try:
        data = download_data(ticker)
        close = data['Close']
        
        # Calculate Indicators (Deterministic)
        sma_20 = calculate_sma(close, 20)
        sma_50 = calculate_sma(close, 50)
        ema_20 = calculate_ema(close, 20)
        rsi = calculate_rsi(close, 14)
        macd, macd_signal = calculate_macd(close)
        upper_bb, lower_bb = calculate_bollinger_bands(close)
        
        # Get latest values
        latest = data.index[-1]
        
        result = {
            "source": "Alpha Vantage" if "Alpha Vantage" in str(data) else "YFinance", # Simple check, or better flag? 
            "ticker": ticker,
            "date": str(latest.date()),
            "price": float(close.iloc[-1]),
            "indicators": {
                "SMA_20": float(sma_20.iloc[-1]),
                "SMA_50": float(sma_50.iloc[-1]),
                "EMA_20": float(ema_20.iloc[-1]),
                "RSI": float(rsi.iloc[-1]),
                "MACD": float(macd.iloc[-1]),
                "MACD_Signal": float(macd_signal.iloc[-1]),
                "Bollinger_Upper": float(upper_bb.iloc[-1]),
                "Bollinger_Lower": float(lower_bb.iloc[-1])
            },
            "signals": {}
        }
        
        # Basic Signal Interpretation
        signals = []
        if result["indicators"]["RSI"] < 30:
            signals.append("RSI Oversold (Bullish)")
        elif result["indicators"]["RSI"] > 70:
            signals.append("RSI Overbought (Bearish)")
            
        if result["indicators"]["SMA_20"] > result["indicators"]["SMA_50"]:
             signals.append("Golden Trend (SMA20 > SMA50)")
        elif result["indicators"]["SMA_20"] < result["indicators"]["SMA_50"]:
             signals.append("Death Trend (SMA20 < SMA50)")
             
        result["signals"] = signals
        
        # Determine trend for frontend
        trend = "Sideways"
        if result["indicators"]["SMA_20"] > result["indicators"]["SMA_50"]:
            trend = "Uptrend"
        elif result["indicators"]["SMA_20"] < result["indicators"]["SMA_50"]:
            trend = "Downtrend"
        
        # Store technical analysis in state for frontend
        tool_context.state["technical_analysis"] = {
            "trend": trend,
            "rsi": round(result["indicators"]["RSI"], 2),
            "macd": "Bullish" if result["indicators"]["MACD"] > result["indicators"]["MACD_Signal"] else "Bearish",
            "support_levels": [round(result["indicators"]["Bollinger_Lower"], 2)],
            "resistance_levels": [round(result["indicators"]["Bollinger_Upper"], 2)],
            "rating": min(10, max(0, round((100 - abs(result["indicators"]["RSI"] - 50)) / 10, 1))),
            "price": result["price"],
            # New fields for frontend
            "sma_20": round(result["indicators"]["SMA_20"], 2),
            "sma_50": round(result["indicators"]["SMA_50"], 2),
            "bollinger_upper": round(result["indicators"]["Bollinger_Upper"], 2),
            "bollinger_lower": round(result["indicators"]["Bollinger_Lower"], 2),
        }
        
        return str(result)

    except Exception as e:
        return f"Error calculating indicators for {ticker}: {str(e)}"

# Create FunctionTool instance
get_technical_indicators = FunctionTool(func=get_technical_indicators_func)


# ========================================================================
#  ISOLATED: Price Timeseries Snapshot (NOT an agent tool)
#  - No tool_context, no FunctionTool, no pipeline interaction
#  - Called exclusively via FastAPI REST endpoint
# ========================================================================

import time as _time

_snapshot_cache: dict[tuple[str, str], tuple[float, dict]] = {}
_mcap_cache: dict[str, tuple[float, float | None, str]] = {}  # ticker -> (timestamp, market_cap, currency)
_SNAPSHOT_TTL = 60  # seconds

_TIMEFRAME_MAP = {
    "1D":  {"period": "1d",  "interval": "5m"},
    "5D":  {"period": "5d",  "interval": "15m"},
    "1M":  {"period": "1mo", "interval": "1h"},
    "6M":  {"period": "6mo", "interval": "1d"},
    "YTD": {"period": "ytd", "interval": "1d"},
    "1Y":  {"period": "1y",  "interval": "1d"},
    "5Y":  {"period": "5y",  "interval": "1wk"},
}


def get_price_timeseries_snapshot(ticker: str, timeframe: str) -> dict:
    """
    Fetch lightweight OHLC timeseries for a price chart.
    Completely isolated — no agent, no tool_context, no indicators.

    Args:
        ticker: Stock ticker (e.g. 'AAPL').
        timeframe: One of '1D', '5D', '1M', '6M', 'YTD', '1Y', '5Y'.

    Returns:
        Dict with ticker, timeframe, currency, price, change, change_percent,
        timestamps (ISO), and prices (float list).
    """
    key = (ticker.strip().upper(), timeframe.upper())

    # Cache check
    now = _time.time()
    if key in _snapshot_cache:
        cached_at, cached_data = _snapshot_cache[key]
        if now - cached_at < _SNAPSHOT_TTL:
            return cached_data

    tf = _TIMEFRAME_MAP.get(key[1])
    if not tf:
        return {"error": f"Invalid timeframe '{timeframe}'. Use: 1D, 5D, 1M, 6M, YTD, 1Y, 5Y."}

    # Fetch currency + market_cap once per ticker (cached separately)
    # NOTE: deferred to AFTER ticker resolution below so Indian stocks resolve correctly
    currency = "USD"
    market_cap = None

    try:
        # ── Ticker resolution (commodity aliases, crypto, Indian exchanges) ──
        resolved_ticker = key[0]

        # Common commodity & crypto aliases → Yahoo Finance symbols
        _TICKER_ALIASES: dict[str, str] = {
            # Commodities (futures)
            "GOLD": "GC=F", "XAUUSD": "GC=F",
            "SILVER": "SI=F", "XAGUSD": "SI=F",
            "OIL": "CL=F", "CRUDE": "CL=F", "CRUDEOIL": "CL=F", "WTI": "CL=F",
            "BRENT": "BZ=F",
            "NATURALGAS": "NG=F", "NATGAS": "NG=F",
            "COPPER": "HG=F",
            "PLATINUM": "PL=F",
            # Crypto (common short names)
            "BTC": "BTC-USD", "BITCOIN": "BTC-USD",
            "ETH": "ETH-USD", "ETHEREUM": "ETH-USD",
            "SOL": "SOL-USD", "SOLANA": "SOL-USD",
            "DOGE": "DOGE-USD", "DOGECOIN": "DOGE-USD",
            "XRP": "XRP-USD", "RIPPLE": "XRP-USD",
            "ADA": "ADA-USD", "CARDANO": "ADA-USD",
            "DOT": "DOT-USD", "AVAX": "AVAX-USD",
            "MATIC": "MATIC-USD", "LINK": "LINK-USD",
            "BNB": "BNB-USD",
            # Forex pairs
            "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X", "USDINR": "USDINR=X",
        }

        # Build candidate list: alias first, then original, then suffixed variants
        candidates: list[str] = []

        alias = _TICKER_ALIASES.get(key[0])
        if alias:
            candidates.append(alias)
        candidates.append(key[0])  # original as-is

        # If no special chars (not already =F, -USD, .NS etc.) → try suffixes
        # Order: Indian exchanges first (more common), then crypto
        if "." not in key[0] and "=" not in key[0] and "-" not in key[0]:
            candidates.append(f"{key[0]}.NS")    # Indian NSE
            candidates.append(f"{key[0]}.BO")    # Indian BSE
            candidates.append(f"{key[0]}-USD")   # crypto fallback (last)

        # Deduplicate while preserving order
        seen: set[str] = set()
        suffixes_to_try: list[str] = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                suffixes_to_try.append(c)

        df = pd.DataFrame()
        for candidate in suffixes_to_try:
            df = yf.download(
                candidate,
                period=tf["period"],
                interval=tf["interval"],
                auto_adjust=True,
                progress=False,
            )
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if not df.empty and "Close" in df.columns and not df["Close"].isna().all():
                resolved_ticker = candidate
                break

        if df.empty or "Close" not in df.columns:
            return {"error": f"No data returned for {key[0]} ({key[1]}). Tried: {', '.join(suffixes_to_try)}"}

        # Now resolve currency + market_cap using the working ticker
        if resolved_ticker in _mcap_cache and (now - _mcap_cache[resolved_ticker][0]) < _SNAPSHOT_TTL:
            _, market_cap, currency = _mcap_cache[resolved_ticker]
        else:
            try:
                info = yf.Ticker(resolved_ticker).fast_info
                currency = getattr(info, "currency", "USD") or "USD"
                market_cap = getattr(info, "market_cap", None)
                if market_cap is not None:
                    market_cap = float(market_cap)
                _mcap_cache[resolved_ticker] = (now, market_cap, currency)
            except Exception:
                _mcap_cache[resolved_ticker] = (now, None, "USD")

        # Drop NaN rows and sort chronologically
        df = df.dropna(subset=["Close"]).sort_index()

        closes = df["Close"].tolist()
        timestamps = [
            t.isoformat() if hasattr(t, "isoformat") else str(t) for t in df.index
        ]

        current_price = round(float(closes[-1]), 4)
        open_price = float(closes[0])
        change = round(current_price - open_price, 4)
        change_pct = round((change / open_price) * 100, 2) if open_price != 0 else 0.0

        result = {
            "ticker": resolved_ticker,
            "timeframe": key[1],
            "currency": currency,
            "price": current_price,
            "change": change,
            "change_percent": change_pct,
            "market_cap": market_cap,
            "timestamps": timestamps,
            "prices": [round(float(p), 4) for p in closes],
        }

        # Store in cache
        _snapshot_cache[key] = (now, result)
        return result

    except Exception as e:
        return {"error": f"Snapshot fetch failed for {key[0]}: {str(e)}"}
