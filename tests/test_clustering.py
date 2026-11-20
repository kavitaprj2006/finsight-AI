"""
Unit Tests for Market Regime Clustering Engine
"""
import pytest
import numpy as np
import pandas as pd
from app.ml.clustering import MarketRegimeDetector

def test_regime_clustering_execution(sample_ohlcv_df):
    detector = MarketRegimeDetector(n_clusters=3)
    res = detector.fit_predict(sample_ohlcv_df)

    assert "features_df" in res
    assert "labels" in res
    assert "profiles" in res
    assert "transition_matrix" in res
    assert "current_regime" in res

    profiles = res["profiles"]
    assert len(profiles) == 3
    for c, p in profiles.items():
        assert "name" in p
        assert "mean_return_pct" in p
        assert "annualized_vol_pct" in p
        assert "frequency_pct" in p
        assert p["count"] > 0
