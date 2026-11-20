"""
FinSight AI - Technical Indicators Implementation
Formulas computed on OHLCV pandas DataFrames without external black-box indicator libraries.
"""
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd

def compute_sma(series: pd.Series, window: int = 20) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=window, min_periods=1).mean()

def compute_ema(series: pd.Series, span: int = 20) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=span, adjust=False).mean()

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (RSI) using Wilder's exponential smoothing.
    """
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # First average using simple mean
    avg_gain = gain.ewm(alpha=1.0/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """
    Moving Average Convergence Divergence (MACD).
    Returns MACD Line, Signal Line, and MACD Histogram.
    """
    fast_ema = compute_ema(series, span=fast)
    slow_ema = compute_ema(series, span=slow)
    macd_line = fast_ema - slow_ema
    signal_line = compute_ema(macd_line, span=signal)
    hist = macd_line - signal_line
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": hist
    }

def compute_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
    """
    Bollinger Bands: Middle (SMA), Upper (+N std), Lower (-N std).
    """
    sma = compute_sma(series, window=window)
    rolling_std = series.rolling(window=window, min_periods=1).std().fillna(0.0)
    upper = sma + (rolling_std * num_std)
    lower = sma - (rolling_std * num_std)
    bandwidth = (upper - lower) / (sma + 1e-10)
    return {
        "middle": sma,
        "upper": upper,
        "lower": lower,
        "bandwidth": bandwidth
    }

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (ATR)."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0/period, min_periods=period, adjust=False).mean()
    return atr

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes all standard indicators and appends them to a copy of the dataframe.
    """
    df = df.copy()
    close = df["Close"]

    df["SMA_20"] = compute_sma(close, window=20)
    df["SMA_50"] = compute_sma(close, window=50)
    df["SMA_200"] = compute_sma(close, window=200)

    df["EMA_12"] = compute_ema(close, span=12)
    df["EMA_26"] = compute_ema(close, span=26)

    df["RSI_14"] = compute_rsi(close, period=14)

    macd_dict = compute_macd(close, fast=12, slow=26, signal=9)
    df["MACD"] = macd_dict["macd"]
    df["MACD_Signal"] = macd_dict["signal"]
    df["MACD_Hist"] = macd_dict["histogram"]

    bb_dict = compute_bollinger_bands(close, window=20, num_std=2.0)
    df["BB_Upper"] = bb_dict["upper"]
    df["BB_Middle"] = bb_dict["middle"]
    df["BB_Lower"] = bb_dict["lower"]

    if "High" in df.columns and "Low" in df.columns:
        df["ATR_14"] = compute_atr(df, period=14)

    # Daily Return and Rolling Volatility (21-day annualized)
    df["Daily_Return"] = close.pct_change()
    df["Rolling_Vol_21"] = df["Daily_Return"].rolling(21, min_periods=5).std() * np.sqrt(252)

    return df
