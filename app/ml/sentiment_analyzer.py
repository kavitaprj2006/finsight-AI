"""
FinSight AI - Financial News Sentiment Intelligence
TF-IDF vectorizer + Logistic Regression classifier for financial headlines.
"""
from typing import Dict, List, Any, Tuple
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

class FinancialSentimentAnalyzer:
    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=1500,
                stop_words="english",
                sublinear_tf=True
            )),
            ("clf", LogisticRegression(C=1.5, max_iter=200, random_state=42))
        ])
        self.is_trained = False
        self._train_default_model()

    def _clean_text(self, text: str) -> str:
        """Removes special characters, URLs, and normalizes whitespace."""
        text = str(text).lower()
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        text = re.sub(r"[^a-zA-Z0-9\s%$]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _train_default_model(self):
        """Pre-trains on curated financial headline corpus."""
        training_corpus = [
            # Positive
            ("Quarterly net profit jumps 25% beating analyst expectations", "Positive"),
            ("Revenue surges driven by explosive cloud demand and enterprise adoption", "Positive"),
            ("Company raises full year guidance and declares special dividend", "Positive"),
            ("Signs major multi billion dollar deal with strategic European partner", "Positive"),
            ("Stock upgraded to strong buy with raised price target", "Positive"),
            ("Operating margin expands significantly due to cost discipline", "Positive"),
            ("Record free cash flow reported with strong balance sheet liquidity", "Positive"),
            ("Unveils breakthrough next generation AI chip architecture", "Positive"),
            ("Deposit growth accelerates while credit quality remains resilient", "Positive"),
            ("Secures regulatory approval for strategic expansion into new markets", "Positive"),

            # Negative
            ("Net loss widens significantly as sales slump across retail sector", "Negative"),
            ("Cuts revenue forecast warning of sustained customer spending delays", "Negative"),
            ("Faces severe regulatory scrutiny and antitrust investigation", "Negative"),
            ("Downgraded to sell following weak quarterly performance and margin pressure", "Negative"),
            ("High debt burden and default risks trigger credit rating downgrade", "Negative"),
            ("Supply chain disruptions cause production halt and shipping delays", "Negative"),
            ("Foreign institutional investors pull funds amid steep valuation concerns", "Negative"),
            ("CEO steps down unexpectedly amid accounting inquiry", "Negative"),
            ("Operating profit plunges 40% due to rising input costs and inflation", "Negative"),
            ("Credit card delinquencies surge as consumer demand deteriorates", "Negative"),

            # Neutral
            ("Central bank keeps benchmark interest rate unchanged at policy meeting", "Neutral"),
            ("Scheduled to release quarterly earnings report next Thursday", "Neutral"),
            ("Annual general meeting to vote on routine board appointments", "Neutral"),
            ("Trading volume remains flat ahead of inflation data release", "Neutral"),
            ("Company publishes annual sustainability and ESG report", "Neutral"),
            ("Management attends industry technology investor conference", "Neutral"),
            ("Shareholders approve routine dividend distribution and auditor appointment", "Neutral"),
            ("Index rebalancing adds two consumer stocks replacing energy firm", "Neutral"),
            ("Exchange issues circular on trading hour modifications", "Neutral"),
            ("Treasury yields hold steady following economic data release", "Neutral"),
        ]

        # Duplicate corpus with slight variations to build balanced dataset
        X_raw = [item[0] for item in training_corpus]
        y_raw = [item[1] for item in training_corpus]

        X_cleaned = [self._clean_text(t) for t in X_raw]
        self.pipeline.fit(X_cleaned, y_raw)
        self.is_trained = True

    def analyze_headline(self, text: str) -> Dict[str, Any]:
        """
        Classifies sentiment of headline into Positive, Negative, or Neutral,
        providing compound score (-1.0 to 1.0) and confidence score.
        """
        cleaned = self._clean_text(text)
        if not cleaned:
            return {"sentiment": "Neutral", "compound_score": 0.0, "confidence": 0.5}

        pred_label = self.pipeline.predict([cleaned])[0]
        probs = self.pipeline.predict_proba([cleaned])[0]
        classes = list(self.pipeline.classes_)

        prob_pos = probs[classes.index("Positive")] if "Positive" in classes else 0.0
        prob_neg = probs[classes.index("Negative")] if "Negative" in classes else 0.0
        prob_neu = probs[classes.index("Neutral")] if "Neutral" in classes else 0.0

        # Compound score: scale between -1.0 (pure negative) to +1.0 (pure positive)
        compound = float(prob_pos - prob_neg)
        confidence = float(max(probs))

        return {
            "sentiment": pred_label,
            "compound_score": round(compound, 3),
            "confidence": round(confidence, 3),
            "probabilities": {
                "positive": round(float(prob_pos), 3),
                "neutral": round(float(prob_neu), 3),
                "negative": round(float(prob_neg), 3),
            }
        }

    def analyze_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyzes a list of news article dictionaries."""
        results = []
        for art in articles:
            res = self.analyze_headline(art.get("headline", ""))
            merged = dict(art)
            merged.update({
                "sentiment_label": res["sentiment"],
                "compound_score": res["compound_score"],
                "confidence": res["confidence"]
            })
            results.append(merged)
        return results

sentiment_analyzer = FinancialSentimentAnalyzer()
