"""
Signal Processing Utilities for Financial Time Series.
Includes Hampel Filter (Outlier Removal) and Wavelet Denoising.
"""

import numpy as np
import pandas as pd
import pywt
from scipy import signal

def hampel_filter(series: pd.Series, window_size: int = 5, n_sigmas: int = 3) -> pd.Series:
    """
    Apply Hampel Filter to remove outliers.
    Replaces outliers with the rolling median.
    
    Args:
        series: Time series data (prices).
        window_size: Rolling window size (half-width). Reduced to 5 for less lag.
        n_sigmas: Number of standard deviations (MADs) to identify outliers.
    """
    n = len(series)
    new_series = series.copy()
    k = 1.4826  # Scale factor for Gaussian distribution
    
    # Calculate rolling median and MAD
    rolling_median = series.rolling(window=2*window_size, center=True).median()
    rolling_mad = k * series.rolling(window=2*window_size, center=True).apply(
        lambda x: np.median(np.abs(x - np.median(x)))
    )
    
    # Identify outliers
    difference = np.abs(series - rolling_median)
    outlier_indices = difference > (n_sigmas * rolling_mad)
    
    # Replace outliers
    new_series[outlier_indices] = rolling_median[outlier_indices]
    
    # Handle NaNs from rolling (fill with original)
    new_series.fillna(series, inplace=True)
    
    return new_series

def wavelet_denoising(series: pd.Series, wavelet: str = 'db4', level: int = 1) -> pd.Series:
    """
    Apply Discrete Wavelet Transform (DWT) denoising.
    Uses 'db4' wavelet by default, suitable for financial trends.
    """
    # Adaptive level: deeper decomposition for longer series, but cap at 3
    max_level = pywt.dwt_max_level(len(series), pywt.Wavelet(wavelet).dec_len)
    level = min(max(1, max_level - 1), 3)

    # Decompose
    coeff = pywt.wavedec(series, wavelet, mode="per", level=level)
    
    # Calculate threshold — REDUCED from 0.8 to 0.45 to preserve stock-specific dynamics.
    # The universal threshold at 0.8 was flattening all stocks into similar gentle curves.
    sigma = (1/0.6745) * np.median(np.abs(coeff[-1] - np.median(coeff[-1])))
    ut_thresh = sigma * np.sqrt(2 * np.log(len(series))) * 0.45  # Keep more signal detail
    
    # Thresholding
    coeff[1:] = (pywt.threshold(i, value=ut_thresh, mode='soft') for i in coeff[1:])
    
    # Reconstruct
    denoised = pywt.waverec(coeff, wavelet, mode="per")
    
    # Match length (sometimes reconstruction is slightly longer)
    if len(denoised) > len(series):
        denoised = denoised[:len(series)]
    elif len(denoised) < len(series):
        # This rarely happens with 'per' mode, but safe padding
        denoised = np.pad(denoised, (0, len(series)-len(denoised)), 'edge')

    return pd.Series(denoised, index=series.index)

def prepare_for_timesfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full preprocessing pipeline:
    1. Hampel Filter (Outliers)
    2. Wavelet Denoising (Noise)
    3. Log-Return Calculation (Stationarity)
    """
    if 'Close' not in df.columns:
        raise ValueError("DataFrame must contain 'Close' prediction.")
        
    prices = df['Close']
    
    # Step 1: Hampel
    clean_prices = hampel_filter(prices)
    
    # Step 2: Wavelet
    denoised_prices = wavelet_denoising(clean_prices)
    
    # --- STEP 3: ANCHOR TO REALITY (Proportional Bias Correction) ---
    # Issue: Denoising smooths recent moves, causing a level mismatch.
    # Fix: Proportional (multiplicative) correction preserves relative dynamics
    # instead of a uniform additive shift that destroys volatility shape.
    last_real = prices.iloc[-1]
    last_smoothed = denoised_prices.iloc[-1]
    
    if last_smoothed != 0 and not np.isnan(last_smoothed):
        ratio = last_real / last_smoothed
        final_prices = denoised_prices * ratio
    else:
        # Fallback to additive if smoothed is zero/nan
        final_prices = denoised_prices + (last_real - last_smoothed)
    
    # Step 4: Log Returns (Optional, kept for reference structure)
    log_returns = np.log(final_prices / final_prices.shift(1))
    
    result = df.copy()
    result['Clean_Close'] = final_prices # Now anchored to T_0
    result['Log_Returns'] = log_returns
    
    return result.dropna()
