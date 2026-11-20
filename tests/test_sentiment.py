"""
Unit Tests for Financial News Sentiment NLP Analyzer
"""
import pytest
from app.ml.sentiment_analyzer import FinancialSentimentAnalyzer

def test_financial_sentiment_predictions():
    analyzer = FinancialSentimentAnalyzer()

    # Clear positive test
    pos_res = analyzer.analyze_headline("Company reports record profit jump of 35% with surging dividend")
    assert pos_res["sentiment"] == "Positive"
    assert pos_res["compound_score"] > 0.0

    # Clear negative test
    neg_res = analyzer.analyze_headline("Net loss widens sharply amid regulatory investigation and credit downgrade")
    assert neg_res["sentiment"] == "Negative"
    assert neg_res["compound_score"] < 0.0

    # Neutral test
    neu_res = analyzer.analyze_headline("Central bank keeps interest rate unchanged at policy meeting")
    assert neu_res["sentiment"] in ("Neutral", "Positive")

def test_sentiment_batch_processing():
    analyzer = FinancialSentimentAnalyzer()
    articles = [
        {"headline": "Tech earnings surge above Wall Street consensus", "symbol": "AAPL"},
        {"headline": "Antitrust lawsuit filed against tech conglomerate", "symbol": "GOOGL"},
    ]
    results = analyzer.analyze_batch(articles)
    assert len(results) == 2
    assert "sentiment_label" in results[0]
    assert "compound_score" in results[0]
