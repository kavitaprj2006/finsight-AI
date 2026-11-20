# FinSight AI - Machine Learning Model Evaluation & Methodology

This document outlines the machine learning validation methodology, feature pipelines, and benchmark comparisons implemented in FinSight AI.

---

## 1. Machine Learning Philosophy & Guardrails

FinSight AI explicitly adheres to financial engineering standards:
1. **Zero Look-Ahead Bias**: Observations at time $t$ contain feature values computed solely using data available at or before time $t$ ($\{P_\tau\}_{\tau \le t}$).
2. **Strict Chronological Splits**: Time-series observations are never randomly shuffled. Train and test partitions are split strictly along the time axis ($T_{\text{train}} < T_{\text{test}}$).
3. **No Target Leakage**: The target return is calculated strictly over the forward window $[t, t+h]$ and shifted backwards to align with features at time $t$. Any trailing rows with unknown future returns are dropped during training.
4. **Transparent Probabilities**: Predictive models present confidence intervals and error deviations rather than guaranteed point forecasts.

---

## 2. Supervised Regression (Forward Return Prediction)

### Task
Predict continuous forward returns:
$$y_t^{\text{reg}} = \frac{\text{Close}_{t+h} - \text{Close}_t}{\text{Close}_t}$$
for horizons $h = 5$ days (~1 week) and $h = 20$ days (~1 month).

### Models Evaluated
- **Baseline**: Ridge Regression (L2-regularized linear model with Standard Scaler).
- **Ensemble Tree**: Random Forest Regressor (100 estimators, max depth 6, min samples split 5).
- **Gradient Boosting**: XGBoost Regressor (100 estimators, learning rate 0.05, subsample 0.8).

### Evaluation Metrics
- **Mean Absolute Error (MAE)**: Measures average magnitude of return prediction errors.
- **Root Mean Squared Error (RMSE)**: Penalizes large outlier forecast errors.
- **$R^2$ Score**: Out-of-sample variance explained relative to mean return baseline.
- **Directional Accuracy**: Proportion of observations where the sign of the forecast matched the sign of the actual return:
  $$\text{DA} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\text{sign}(\hat{y}_i) == \text{sign}(y_i))$$

---

## 3. Supervised Classification (Market Direction)

### Task
Predict forward market direction:
$$y_t^{\text{clf}} = \begin{cases} 1 & \text{if } y_t^{\text{reg}} > 0 \\ 0 & \text{otherwise} \end{cases}$$

### Models Evaluated
- **Baseline**: Logistic Regression with L2 regularization.
- **Ensemble Tree**: Random Forest Classifier.
- **Gradient Boosting**: XGBoost Classifier with log-loss optimization.

### Evaluation Metrics
- **Accuracy**: Overall fraction of correct direction calls.
- **Precision**: $\frac{\text{TP}}{\text{TP} + \text{FP}}$ (reliability of bullish calls).
- **Recall**: $\frac{\text{TP}}{\text{TP} + \text{FN}}$ (capture rate of upward moves).
- **F1 Score**: Harmonic mean of Precision and Recall.
- **ROC-AUC**: Receiver Operating Characteristic Area Under Curve.

---

## 4. Unsupervised Market Regime Detection

- **Algorithm**: K-Means Clustering on standardized 21-day rolling returns, 21-day annualized volatility, 10-day momentum, drawdown, and volume ratios.
- **Cluster Selection**: Silhouette score evaluation across $k \in [2, 5]$.
- **Statistical Interpretation**:
  - **Bullish - Low Volatility**: Positive mean return with below-average volatility.
  - **Bearish - High Volatility**: Negative mean return with elevated volatility.
  - **Expansion - High Volatility**: Strong upward drift with high momentum and volume.
  - **Consolidation / Neutral**: Range-bound sideways action with compressed returns.
