"""
FinSight AI - Market Regime Detection Engine
Discovers latent market regimes using K-Means clustering on volatility, momentum, and drawdown.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from app.analytics.technical_indicators import compute_all_indicators
from app.analytics.risk_metrics import calculate_drawdown
from app.core.logger import logger

class MarketRegimeDetector:
    def __init__(self, n_clusters: int = 3, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        self.feature_names = [
            "Rolling_Return_21",
            "Rolling_Vol_21",
            "Momentum_10",
            "Drawdown",
            "Volume_Ratio"
        ]

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts regime clustering features from price series."""
        df = compute_all_indicators(df).copy()
        close = df["Close"]

        df["Rolling_Return_21"] = close.pct_change(21)
        df["Rolling_Vol_21"] = df["Daily_Return"].rolling(21, min_periods=5).std() * np.sqrt(252)
        df["Momentum_10"] = close.pct_change(10)
        
        dd_res = calculate_drawdown(close)
        df["Drawdown"] = dd_res["drawdown_series"]

        vol_sma = df["Volume"].rolling(20, min_periods=1).mean()
        df["Volume_Ratio"] = df["Volume"] / (vol_sma + 1e-10)

        feature_df = df[self.feature_names].dropna()
        return feature_df

    def find_optimal_clusters(self, X: pd.DataFrame, max_k: int = 6) -> Dict[int, float]:
        """Evaluates silhouette scores for k in range 2 to max_k."""
        X_scaled = self.scaler.fit_transform(X)
        scores = {}
        for k in range(2, min(max_k + 1, len(X))):
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=5)
            labels = km.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            scores[k] = float(score)
        return scores

    def fit_predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Fits K-Means and interprets regime profiles statistically.
        """
        features_df = self.prepare_features(df)
        if len(features_df) < 50:
            raise ValueError(f"Insufficient data for regime clustering: {len(features_df)} rows.")

        X_scaled = self.scaler.fit_transform(features_df)
        labels = self.kmeans.fit_predict(X_scaled)
        features_df["Regime"] = labels

        # Interpret clusters using statistical profiles
        cluster_profiles = {}
        for c in range(self.n_clusters):
            c_data = features_df[features_df["Regime"] == c]
            mean_ret = float(c_data["Rolling_Return_21"].mean() * 100.0) # in %
            mean_vol = float(c_data["Rolling_Vol_21"].mean() * 100.0)    # in %
            mean_dd = float(c_data["Drawdown"].mean() * 100.0)          # in %
            freq_pct = float(len(c_data) / len(features_df) * 100.0)

            # Assign empirical label based on measurements
            if mean_ret > 0 and mean_vol < features_df["Rolling_Vol_21"].mean() * 100.0:
                label = "Bullish - Low Volatility"
                color = "#22C997" # Positive
            elif mean_ret < 0 and mean_vol >= features_df["Rolling_Vol_21"].mean() * 100.0:
                label = "Bearish - High Volatility"
                color = "#F06470" # Negative
            elif mean_ret > 0 and mean_vol >= features_df["Rolling_Vol_21"].mean() * 100.0:
                label = "Expansion - High Volatility"
                color = "#4B9BFF" # Accent
            else:
                label = "Consolidation / Neutral"
                color = "#F2B75A" # Warning

            cluster_profiles[c] = {
                "name": label,
                "color": color,
                "mean_return_pct": round(mean_ret, 2),
                "annualized_vol_pct": round(mean_vol, 2),
                "mean_drawdown_pct": round(mean_dd, 2),
                "frequency_pct": round(freq_pct, 1),
                "count": len(c_data)
            }

        # Map named regime back to timeline
        regime_names = [cluster_profiles[l]["name"] for l in labels]
        features_df["Regime_Name"] = regime_names

        # Compute transition matrix
        transition_matrix = pd.crosstab(
            pd.Series(labels[:-1], name="From"),
            pd.Series(labels[1:], name="To"),
            normalize="index"
        ).to_dict()

        return {
            "features_df": features_df,
            "labels": labels,
            "profiles": cluster_profiles,
            "transition_matrix": transition_matrix,
            "current_regime": cluster_profiles[labels[-1]]
        }
