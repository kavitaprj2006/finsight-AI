"""
FinSight AI - Machine Learning Evaluation Suite
Computes MAE, RMSE, R2, Directional Accuracy, Precision, Recall, F1, and ROC-AUC.
"""
from typing import Dict, Any, Optional
import numpy as np
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)

def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Evaluates continuous return predictions against actual forward returns.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = float(mean_absolute_error(y_true, y_pred))
    # In scikit-learn, root_mean_squared_error is preferred or np.sqrt(mean_squared_error)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))

    # Directional Accuracy: Did predicted sign match actual sign?
    dir_match = (np.sign(y_pred) == np.sign(y_true)).astype(int)
    dir_acc = float(np.mean(dir_match))

    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "directional_accuracy": dir_acc
    }

def evaluate_classification(y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Evaluates market direction classification predictions.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    roc_auc = 0.5
    if y_prob is not None:
        try:
            # Handle binary probabilities
            probs = y_prob[:, 1] if len(y_prob.shape) > 1 and y_prob.shape[1] > 1 else y_prob
            roc_auc = float(roc_auc_score(y_true, probs))
        except Exception:
            roc_auc = 0.5

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_auc
    }
