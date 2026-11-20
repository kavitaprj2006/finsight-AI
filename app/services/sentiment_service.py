"""
FinSight AI - News & Sentiment Service
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from app.data_providers.factory import get_market_data_provider
from app.ml.sentiment_analyzer import sentiment_analyzer

class SentimentService:
    def __init__(self):
        self.provider = get_market_data_provider()

    def get_news_with_sentiment(self, symbol: Optional[str] = None, market: str = "IN", limit: int = 15) -> Dict[str, Any]:
        resp = self.provider.get_news(symbol=symbol, market=market, limit=limit)
        articles = resp.data if resp.is_success and resp.data is not None else []

        analyzed_articles = sentiment_analyzer.analyze_batch(articles)

        # Aggregate metrics
        pos_count = sum(1 for a in analyzed_articles if a.get("sentiment_label") == "Positive")
        neg_count = sum(1 for a in analyzed_articles if a.get("sentiment_label") == "Negative")
        neu_count = sum(1 for a in analyzed_articles if a.get("sentiment_label") == "Neutral")
        total = len(analyzed_articles)

        avg_compound = (
            sum(a.get("compound_score", 0.0) for a in analyzed_articles) / total
            if total > 0 else 0.0
        )

        return {
            "articles": analyzed_articles,
            "total_count": total,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
            "positive_pct": round((pos_count / total * 100.0) if total else 0.0, 1),
            "negative_pct": round((neg_count / total * 100.0) if total else 0.0, 1),
            "neutral_pct": round((neu_count / total * 100.0) if total else 0.0, 1),
            "avg_compound_score": round(avg_compound, 3),
            "provider": resp.provider,
            "is_sample": resp.is_sample
        }

sentiment_service = SentimentService()
