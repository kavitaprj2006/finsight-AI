"""
Unit Tests for Market Direction Classification Models (Logistic, Random Forest, XGBoost)
"""
import pytest
import numpy as np
import pandas as pd
from app.ml.feature_engineering import generate_ml_features, train_test_split_temporal
from app.ml.classification_models import MarketDirectionClassifierSuite

def test_classification_suite_training(sample_ohlcv_df):
    X, _, y_clf = generate_ml_features(sample_ohlcv_df, horizon=5)
    X_train, X_test, y_train, y_test = train_test_split_temporal(X, y_clf, train_ratio=0.80)

    suite = MarketDirectionClassifierSuite()
    output = suite.fit_and_evaluate(X_train, y_train, X_test, y_test)

    assert "comparison" in output
    assert "best_model_name" in output

    comp = output["comparison"]
    for m in ["Logistic Regression (Baseline)", "Random Forest Classifier", "XGBoost Classifier"]:
        assert m in comp
        assert "accuracy" in comp[m]
        assert "f1" in comp[m]
        assert "roc_auc" in comp[m]
        assert 0.0 <= comp[m]["accuracy"] <= 1.0

    # Prediction test
    preds, probs = suite.predict(output["best_model_name"], X_test)
    assert len(preds) == len(X_test)
    assert len(probs) == len(X_test)
