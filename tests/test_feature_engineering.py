"""
Unit Tests for Machine Learning Feature Engineering and Data Leakage Prevention
"""
import pytest
import numpy as np
import pandas as pd
from app.ml.feature_engineering import generate_ml_features, train_test_split_temporal

def test_feature_generation_and_target_alignment(sample_ohlcv_df):
    horizon = 5
    X, y_reg, y_clf = generate_ml_features(sample_ohlcv_df, horizon=horizon)

    # 1. Row alignment: X, y_reg, and y_clf must share the exact same length and index
    assert len(X) == len(y_reg) == len(y_clf)
    assert (X.index == y_reg.index).all()

    # 2. No NaN values in feature matrix
    assert not X.isna().any().any()
    assert not y_reg.isna().any()
    assert not y_clf.isna().any()

    # 3. Binary target classification definition
    assert set(y_clf.unique()).issubset({0, 1})
    # Target classification is 1 if y_reg > 0 else 0
    np.testing.assert_array_equal(y_clf.values, (y_reg > 0.0).astype(int).values)

def test_temporal_train_test_split_no_leakage(sample_ohlcv_df):
    X, y_reg, y_clf = generate_ml_features(sample_ohlcv_df, horizon=5)
    X_train, X_test, y_train, y_test = train_test_split_temporal(X, y_reg, train_ratio=0.75)

    # Chronological invariant: Max date in train MUST be strictly less than min date in test
    assert X_train.index.max() < X_test.index.min()
    assert len(X_train) + len(X_test) == len(X)
    assert len(y_train) + len(y_test) == len(y_reg)
