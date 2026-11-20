"""
FinSight AI - Return Regression Models
Trains Linear Regression, Random Forest, and XGBoost to forecast 5-day and 20-day returns.
"""
from typing import Dict, Any, Tuple, Optional
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from app.ml.evaluation import evaluate_regression
from app.core.logger import logger

class ReturnRegressionSuite:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models = {
            "Ridge Regression (Baseline)": Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", Ridge(alpha=1.0, random_state=random_state))
            ]),
            "Random Forest Regressor": RandomForestRegressor(
                n_estimators=100, max_depth=6, min_samples_split=5,
                random_state=random_state, n_jobs=-1
            ),
            "XGBoost Regressor": XGBRegressor(
                n_estimators=100, max_depth=4, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                random_state=random_state, n_jobs=-1
            )
        }
        self.trained_models = {}
        self.evaluation_results = {}
        self.feature_importances = {}

    def fit_and_evaluate(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict[str, Any]:
        """
        Trains all models on X_train, evaluates on out-of-sample X_test.
        """
        results = {}
        feature_names = list(X_train.columns)

        for name, model in self.models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                metrics = evaluate_regression(y_test, y_pred)
                self.trained_models[name] = model
                results[name] = metrics

                # Extract feature importance if available
                if hasattr(model, "feature_importances_"):
                    importances = model.feature_importances_
                    feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
                    self.feature_importances[name] = dict(feat_imp)
                elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("regressor"), "coef_"):
                    coefs = np.abs(model.named_steps["regressor"].coef_)
                    feat_imp = sorted(zip(feature_names, coefs), key=lambda x: x[1], reverse=True)
                    self.feature_importances[name] = dict(feat_imp)

                logger.info(f"Trained {name}: MAE={metrics['mae']:.4f}, R2={metrics['r2']:.4f}")
            except Exception as e:
                logger.error(f"Failed training {name}: {e}")
                results[name] = {"mae": 999.0, "rmse": 999.0, "r2": -999.0, "directional_accuracy": 0.0}

        self.evaluation_results = results
        # Best model based on lowest MAE or highest R2
        best_name = max(results.keys(), key=lambda k: results[k]["r2"])

        return {
            "comparison": results,
            "best_model_name": best_name,
            "best_metrics": results.get(best_name),
            "feature_importances": self.feature_importances.get(best_name, {})
        }

    def predict(self, model_name: str, X: pd.DataFrame) -> np.ndarray:
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} has not been trained yet.")
        return self.trained_models[model_name].predict(X)

    def save_model(self, model_name: str, filepath: str):
        if model_name in self.trained_models:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            joblib.dump(self.trained_models[model_name], filepath)
            logger.info(f"Saved {model_name} to {filepath}")
