"""Tools for the Oracle Predictor Agent - CLEAN SLATE (Simplified)."""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import timedelta
from google.adk.tools import FunctionTool, ToolContext
from app.sub_agents.technical_analyst.tools import download_data
from .signal_processing import prepare_for_timesfm
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper for JSON Serialization of Numpy/Pandas types ---
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (pd.Timestamp, pd.Period)):
            return str(obj)
        return json.JSONEncoder.default(self, obj)
# ... [imports] ...

def clean_and_forecast_func(ticker: str, tool_context: ToolContext) -> str:
    """
    Oracle Prediction Pipeline (v2 - Clean Slate + Signal Processing):
    1. Fetch Raw Data.
    2. Apply Hampel Filter & Wavelet Denoising.
    3. Upload 'Clean_Close' (Denoised Price) to BigQuery.
    4.  Forecast using TimesFM 2.5.
    5.  Return Results (Median + P10/P90 Ribbons).
    
    IMPORTANT: This tool returns INTERMEDIATE data. You MUST proceed to Synthesize this data. 
    DO NOT STOP after this tool.
    """
    # Emit state for frontend
    tool_context.state["pipeline_stage"] = "oracle_forecast"
    tool_context.state["target_ticker"] = ticker
    stages = tool_context.state.get("stages_completed", [])
    if "oracle_forecast" not in stages:
        stages.append("oracle_forecast")
    tool_context.state["stages_completed"] = stages
    
    results = {"ticker": ticker, "status": "failed", "forecast": []}
    
    # --- CONFIGURATION (Loaded from Env) ---
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "custom-ground-482813-s7")
    DATASET_ID = os.environ.get("BQ_DATASET", "trademate_ml")
    # CRITICAL: BigQuery Datasets are Regional (usually us-central1). 
    # Do NOT use 'global' from GOOGLE_CLOUD_LOCATION (which is for Gemini).
    LOCATION = os.environ.get("BQ_LOCATION", "us-central1")
    
    # Validation
    if not PROJECT_ID or not DATASET_ID:
        return json.dumps({"error": "Missing GOOGLE_CLOUD_PROJECT or BQ_DATASET env vars."}, cls=NumpyEncoder)

    try:
        # 1. Fetch Data
        logger.info(f"Oracle: Fetching data for {ticker}...")
        try:
            df = download_data(ticker, period="2y")
        except Exception as e:
            return json.dumps({"error": f"Data Fetch Failed: {str(e)}"}, cls=NumpyEncoder)
            
        last_real_price = float(df['Close'].iloc[-1])
        
        # Compute actual 30-day volatility for smarter fallback bounds
        recent_returns = df['Close'].pct_change().dropna().tail(30)
        daily_vol = float(recent_returns.std()) if len(recent_returns) > 5 else 0.02
        monthly_vol = daily_vol * np.sqrt(30)  # Scale to 30-day horizon
        
        # 2. Advanced Signal Processing
        # User requested Hampel (3 MAD) + Wavelet (db4)
        logger.info("Oracle: Applying Hampel Filter and Wavelet Denoising...")
        try:
            processed_df = prepare_for_timesfm(df)
        except Exception as e:
             logger.warning(f"Signal Processing Warning: {e}. Falling back to raw prices.")
             processed_df = df.copy()
             processed_df['Clean_Close'] = df['Close']
        
        # 3. BigQuery Upload (DENOISED Price)
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
        
        # Sanitized Table Name
        safe_ticker = ticker.replace("-","_").replace("=","_").replace(".","_")
        table_id = f"{PROJECT_ID}.{DATASET_ID}.temp_context_{safe_ticker}"
        
        # Prepare Schema: timestamp, value (Clean_Close), id
        context_df = processed_df.reset_index()[['Date', 'Clean_Close']]
        context_df.columns = ['time_series_timestamp', 'time_series_data']
        context_df['time_series_id'] = ticker
        
        # Clean timestamps
        context_df['time_series_timestamp'] = pd.to_datetime(context_df['time_series_timestamp'])
        
        # Debug Log
        print(f"DEBUG: Uploading {len(context_df)} rows of DENOISED data to {table_id}...")
        
        try:
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",
                schema=[
                    bigquery.SchemaField("time_series_timestamp", "TIMESTAMP"),
                    bigquery.SchemaField("time_series_data", "FLOAT"),
                    bigquery.SchemaField("time_series_id", "STRING"),
                ]
            )
            job = client.load_table_from_dataframe(
                context_df.tail(120), # ~6 months — enough context without diluting recent dynamics
                table_id, 
                job_config=job_config
            )
            job.result()
            print("DEBUG: Upload complete.")
            
        except Exception as e:
            return json.dumps({"error": f"BigQuery Upload Failed: {str(e)} (Check Permissions)"}, cls=NumpyEncoder)
            
        # 3. TimesFM 2.5 Forecast (CORRECT SYNTAX)
        print("DEBUG: Executing AI.FORECAST (TimesFM 2.5)...")
        
        # NOTE: The critical fix is `model => 'TimesFM 2.5'` (Literal String)
        query = f"""
            SELECT *
            FROM AI.FORECAST(
                TABLE `{table_id}`,
                data_col => 'time_series_data',
                timestamp_col => 'time_series_timestamp',
                id_cols => ['time_series_id'],
                model => 'TimesFM 2.5',
                horizon => 30,
                confidence_level => 0.8
            )
        """
        
        try:
            query_job = client.query(query)
            forecast_result = query_job.to_dataframe()
            print("DEBUG: Forecast received from BigQuery!")
            print(f"DEBUG: Columns returned: {list(forecast_result.columns)}")
            
        except GoogleAPICallError as e:
            print(f"DEBUG: BQ Query Error: {e}")
            return json.dumps({"error": f"BigQuery AI.FORECAST Failed: {str(e)}"}, cls=NumpyEncoder)
            
        # 4. Process Results
        future_prices = []
        
        # Determine actual column names (BQ behavior varies)
        cols = list(forecast_result.columns)
        
        # 1. Identify Timestamp Column
        # Prefer exact matches or strong hints
        ts_candidates = [c for c in cols if 'timestamp' in c or 'date' in c]
        ts_col = ts_candidates[0] if ts_candidates else 'time_series_timestamp'
        
        # 2. Identify Value/Data Column
        # Must contain 'data', 'value', 'forecast' BUT NOT 'timestamp' or 'date'
        val_candidates = [
            c for c in cols 
            if ('data' in c or 'value' in c or 'forecast' in c) 
            and ('timestamp' not in c and 'date' not in c)
        ]
        val_col = val_candidates[0] if val_candidates else 'time_series_data'
        
        print(f"DEBUG: Parsed Columns -> Timestamp: '{ts_col}', Value: '{val_col}'")
        
        if ts_col in forecast_result.columns:
             forecast_result = forecast_result.sort_values(ts_col)
             
        for index, row in forecast_result.iterrows():
            # Get values
            predicted_price = row.get(val_col)
            # Try specific names first, then fallback to partial matching
            price_lower = row.get('prediction_interval_lower_bound')
            price_upper = row.get('prediction_interval_upper_bound')
            
            # Volatility-scaled fallback bounds (instead of generic ±10%)
            if predicted_price is None: predicted_price = last_real_price
            if price_lower is None: price_lower = predicted_price * (1 - monthly_vol)
            if price_upper is None: price_upper = predicted_price * (1 + monthly_vol)
            
            future_prices.append({
                "date": str(row[ts_col].date()) if hasattr(row[ts_col], 'date') else str(row[ts_col]),
                "median_price": round(float(predicted_price), 2),
                "ribbon_lower": round(float(price_lower), 2),
                "ribbon_upper": round(float(price_upper), 2)
            })
            
        results["status"] = "success"
        results["forecast"] = future_prices
        results["last_real_price"] = round(last_real_price, 2)
        results["model"] = "TimesFM 2.5 (BigQuery)"
        
        # Store oracle forecast in state for frontend
        if future_prices:
            tool_context.state["oracle_forecast"] = {
                "predicted_price": future_prices[-1]["median_price"] if future_prices else last_real_price,
                "confidence_interval": [future_prices[-1]["ribbon_lower"], future_prices[-1]["ribbon_upper"]] if future_prices else [last_real_price * 0.9, last_real_price * 1.1],
                "model_confidence": 0.8,
                "forecast_horizon": "30 days",
                # Add forecast data for the chart
                "forecast": future_prices,
                # Add historical data for chart context (Last 14 days)
                "history": [
                    {
                        "date": str(idx.date()),
                        "price": round(float(val), 2)
                    }
                    for idx, val in zip(df.index[-14:], df['Close'].iloc[-14:])
                ]
            }
        
    except Exception as e:
        print(f"CRITICAL ERROR in Oracle Tool: {str(e)}")
        results["status"] = "error"
        results["error_message"] = str(e)

    return json.dumps(results, cls=NumpyEncoder)

# Create Tool
clean_and_forecast = FunctionTool(func=clean_and_forecast_func)
