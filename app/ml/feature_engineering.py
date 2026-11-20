"""
FinSight AI - Machine Learning Feature Engineering
Constructs lagged financial features, momentum, volatility, and forward return targets
strictly preserving temporal ordering and eliminating look-ahead bias.
"""
from typing import Tuple, List, Optional
import numpy as np
import pandas as pd
from app.analytics.technical_indicators import compute_all_indicators

def generate_ml_features(df: pd.DataFrame, horizon: int = 5) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Constructs feature matrix X and targets y_reg and y_clf.
    df: OHLCV DataFrame with Date index.
    horizon: Forward prediction horizon in trading days (e.g. 5 or 20).

    Returns:
    X: Feature DataFrame with time-aligned features up to time t.
    y_reg: Forward return (Close[t+h] - Close[t]) / Close[t].
    y_clf: Binary direction (1 if forward return > 0 else 0).
    """
    df = compute_all_indicators(df).copy()
    close = df["Close"]
    volume = df["Volume"]

    # 1. Price Momentum & Lagged Returns
    df["Lag_Return_1"] = df["Daily_Return"].shift(1)
    df["Lag_Return_2"] = df["Daily_Return"].shift(2)
    df["Lag_Return_3"] = df["Daily_Return"].shift(3)
    df["Momentum_5"] = close.pct_change(5)
    df["Momentum_10"] = close.pct_change(10)
    df["Momentum_20"] = close.pct_change(20)

    # 2. Volume Dynamics
    df["Volume_Change"] = volume.pct_change()
    df["Volume_SMA_20"] = volume.rolling(20, min_periods=1).mean()
    df["Volume_Ratio"] = volume / (df["Volume_SMA_20"] + 1e-10)

    # 3. Moving Average Distance
    df["Dist_SMA_20"] = (close - df["SMA_20"]) / (df["SMA_20"] + 1e-10)
    df["Dist_SMA_50"] = (close - df["SMA_50"]) / (df["SMA_50"] + 1e-10)
    df["SMA_Cross"] = (df["SMA_20"] - df["SMA_50"]) / (df["SMA_50"] + 1e-10)

    # 4. Bollinger Band Position (%B)
    bb_range = df["BB_Upper"] - df["BB_Lower"]
    df["BB_Pct"] = (close - df["BB_Lower"]) / (bb_range + 1e-10)

    # 5. Construct Forward Target (Shifted backwards so row t has forward return at t+h)
    forward_close = close.shift(-horizon)
    forward_return = (forward_close - close) / close
    forward_direction = (forward_return > 0.0).astype(int)

    feature_cols = [
        "Daily_Return", "Lag_Return_1", "Lag_Return_2", "Lag_Return_3",
        "Momentum_5", "Momentum_10", "Momentum_20",
        "Volume_Change", "Volume_Ratio",
        "RSI_14", "MACD", "MACD_Signal", "MACD_Hist",
        "Dist_SMA_20", "Dist_SMA_50", "SMA_Cross",
        "BB_Pct", "Rolling_Vol_21"
    ]
    if "ATR_14" in df.columns:
        df["ATR_Norm"] = df["ATR_14"] / close
        feature_cols.append("ATR_Norm")

    # Combine and drop NaNs (including the trailing horizon rows where forward return is unknown)
    data = df[feature_cols].copy()
    data["TARGET_REG"] = forward_return
    data["TARGET_CLF"] = forward_direction

    data = data.dropna()

    X = data[feature_cols]
    y_reg = data["TARGET_REG"]
    y_clf = data["TARGET_CLF"]

    return X, y_reg, y_clf

def train_test_split_temporal(
    X: pd.DataFrame,
    y: pd.Series,
    train_ratio: float = 0.80
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Chronological train-test split.
    Guarantees no data leakage across time boundaries.
    """
    n = len(X)
    split_idx = int(n * train_ratio)

    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]

    return X_train, X_test, y_train, y_test
