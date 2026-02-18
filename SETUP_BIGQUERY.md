# BigQuery ML & TimesFM Setup Guide

To enable the **Oracle-Predictor** to use Google's TimesFM 2.5 model, you must run the following SQL commands in your Google Cloud BigQuery console.

## Prerequisites
1.  **Google Cloud Project**: Selected in console.
2.  **APIs Enabled**: BigQuery API, Vertex AI API.
3.  **Dataset**: Create a dataset named `trademate_ml` (or update code to match).

## Step 1: Create the Connection
You need a generic Cloud Resource connection to access Vertex AI from BigQuery.
1.  Go to BigQuery > **+ ADD** > **Connections to external data sources**.
2.  Type: `Vertex AI remote models, remote functions and BigLake (Cloud Resource)`.
3.  Connection ID: `vertex-ai-conn`.
4.  Region: `us-central1` (Must match your dataset).

CREATE OR REPLACE MODEL `trademate_ml.timesfm_model`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'time_series_timestamp',
  time_series_data_col = 'time_series_data',
  time_series_id_col = 'time_series_id'
);
```

*Note: We are using `ARIMA_PLUS` (Google's enhanced ARIMA with Holiday effects) because `TIMESFM` is currently restricted in your region's public preview. This will still provide high-quality forecasts using the same agent pipeline.*

## Step 3: Grant Permissions
The Service Account created in Step 1 (Connection) needs `Vertex AI User` role.
1.  Copy the Service Account ID from the Connection details.
2.  Go to IAM & Admin.
3.  Grant `Vertex AI User` to that Service Account.
