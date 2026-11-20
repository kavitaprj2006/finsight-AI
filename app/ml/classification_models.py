"""
FinSight AI - Market Direction Classification Models
Trains Logistic Regression, Random Forest, and XGBoost to predict directional return (Up vs Down).
"""
from typing import Dict, Any, Tuple, Optional
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from app.ml.evaluation import evaluate_classification
from app.core.logger import logger

class MarketDirectionClassifierSuite:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models = {
            "Logistic Regression (Baseline)": Pipeline([
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(random_state=random_state, max_iter=500))
            ]),
            "Random Forest Classifier": RandomForestClassifier(
                n_estimators=100, max_depth=5, min_samples_split=5,
                random_state=random_state, n_jobs=-1
            ),
            "XGBoost Classifier": XGBClassifier(
                n_estimators=100, max_depth=3, learning_rate=0.05,
                eval_metric="logloss", random_state=random_state, n_jobs=-1
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
        Trains all classification models and evaluates out-of-sample directional performance.
        """
        results = {}
        feature_names = list(X_train.columns)

        for name, model in self.models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                y_prob = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None
                metrics = evaluate_classification(y_test, y_pred, y_prob)
                self.trained_models[name] = model
                results[name] = metrics

                # Feature importances
                if hasattr(model, "feature_importances_"):
                    importances = model.feature_importances_
                    feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
                    self.feature_importances[name] = dict(feat_imp)
                elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("classifier"), "coef_"):
                    coefs = np.abs(model.named_steps["classifier"].coef_[0])
                    feat_imp = sorted(zip(feature_names, coefs), key=lambda x: x[1], reverse=True)
                    self.feature_importances[name] = dict(feat_imp)

                logger.info(f"Trained {name}: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1']:.4f}, AUC={metrics['roc_auc']:.4f}")
            except Exception as e:
                logger.error(f"Failed training classifier {name}: {e}")
                results[name] = {"accuracy": 0.5, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.5}

        self.evaluation_results = results
        # Best model based on highest F1 score or Accuracy
        best_name = max(results.keys(), key=lambda k: results[k]["accuracy"])

        return {
            "comparison": results,
            "best_model_name": best_name,
            "best_metrics": results.get(best_name),
            "feature_importances": self.feature_importances.get(best_name, {})
        }

    def predict(self, model_name: str, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Returns binary predictions and probability estimates."""
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} has not been trained yet.")
        model = self.trained_models[model_name]
        preds = model.predict(X)
        probs = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else np.ones(len(preds)) * 0.5
        return preds, probs

    def save_model(self, model_name: str, filepath: str):
        if model_name in self.trained_models:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            joblib.dump(self.trained_models[model_name], filepath)
            logger.info(f"Saved {model_name} to {filepath}")
