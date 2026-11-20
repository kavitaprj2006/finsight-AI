"""
Unit Tests for Return Regression Models (Ridge, Random Forest, XGBoost)
"""
import pytest
import numpy as np
import pandas as pd
from app.ml.feature_engineering import generate_ml_features, train_test_split_temporal
from app.ml.regression_models import ReturnRegressionSuite

def test_regression_suite_training(sample_ohlcv_df):
    X, y_reg, _ = generate_ml_features(sample_ohlcv_df, horizon=5)
    X_train, X_test, y_train, y_test = train_test_split_temporal(X, y_reg, train_ratio=0.80)

    suite = ReturnRegressionSuite()
    output = suite.fit_and_evaluate(X_train, y_train, X_test, y_test)

    assert "comparison" in output
    assert "best_model_name" in output
    assert "best_metrics" in output

    comp = output["comparison"]
    for m in ["Ridge Regression (Baseline)", "Random Forest Regressor", "XGBoost Regressor"]:
        assert m in comp
        assert "mae" in comp[m]
        assert "rmse" in comp[m]
        assert "r2" in comp[m]
        assert "directional_accuracy" in comp[m]
        assert comp[m]["mae"] < 1.0  # Returns are fractional e.g. 0.02
