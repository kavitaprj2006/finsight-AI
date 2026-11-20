"""
Unit Tests for Technical Indicators
"""
import pytest
import numpy as np
import pandas as pd
from app.analytics.technical_indicators import (
    compute_sma, compute_ema, compute_rsi,
    compute_macd, compute_bollinger_bands,
    compute_atr, compute_all_indicators
)

def test_sma_and_ema(sample_price_series):
    sma = compute_sma(sample_price_series, window=20)
    ema = compute_ema(sample_price_series, span=20)

    assert len(sma) == len(sample_price_series)
    assert len(ema) == len(sample_price_series)
    assert not sma.isna().any()
    assert not ema.isna().any()

def test_rsi_bounds(sample_price_series):
    rsi = compute_rsi(sample_price_series, period=14)
    assert len(rsi) == len(sample_price_series)
    # RSI must be strictly bounded between 0 and 100
    assert (rsi >= 0.0).all() and (rsi <= 100.0).all()

def test_macd_relationship(sample_price_series):
    macd_dict = compute_macd(sample_price_series, fast=12, slow=26, signal=9)
    assert "macd" in macd_dict
    assert "signal" in macd_dict
    assert "histogram" in macd_dict

    # Histogram must equal MACD - Signal
    diff = macd_dict["macd"] - macd_dict["signal"]
    np.testing.assert_allclose(macd_dict["histogram"].values, diff.values, rtol=1e-5)

def test_bollinger_bands_ordering(sample_price_series):
    bb = compute_bollinger_bands(sample_price_series, window=20, num_std=2.0)
    # Upper Band >= Middle >= Lower Band
    assert (bb["upper"] >= bb["middle"]).all()
    assert (bb["middle"] >= bb["lower"]).all()

def test_compute_all_indicators(sample_ohlcv_df):
    df_res = compute_all_indicators(sample_ohlcv_df)
    expected_cols = [
        "SMA_20", "SMA_50", "SMA_200", "EMA_12", "EMA_26",
        "RSI_14", "MACD", "MACD_Signal", "MACD_Hist",
        "BB_Upper", "BB_Middle", "BB_Lower", "ATR_14",
        "Daily_Return", "Rolling_Vol_21"
    ]
    for col in expected_cols:
        assert col in df_res.columns
