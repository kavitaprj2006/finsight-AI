"""
Unit and Integration Tests for Executive Overview Improvements
Verifies:
1. Missing volatility produces 'N/A' (never an invented 15% fallback).
2. Actual volatility is formatted and displayed correctly with risk regime.
3. Market mover labels accurately describe the tracked universe size.
4. Positive sentiment with sample data displays Positive + Sample (never Live).
5. Negative sentiment with live data displays Negative + Live (never Offline).
6. User ID is dynamically retrieved from repository and passed to service calls.
7. Empty watchlists and empty news are handled gracefully without exceptions.
"""
import importlib
import pytest

overview_mod = importlib.import_module("app.pages.01_overview")
format_volatility_kpi = overview_mod.format_volatility_kpi
get_sentiment_and_provenance_badges = overview_mod.get_sentiment_and_provenance_badges
format_market_movers_header = overview_mod.format_market_movers_header

from app.services.stock_service import stock_service
from app.services.portfolio_service import portfolio_service
from app.database.repository import Repository

def test_missing_volatility_produces_na_not_15():
    """Requirement 1: Missing or None volatility data produces N/A, never silent 15%."""
    # Case A: None risk profile
    kpi_none = format_volatility_kpi(None)
    assert kpi_none["value"] == "N/A"
    assert kpi_none["is_available"] is False
    assert kpi_none["delta"] == "Data calculation unavailable"
    assert kpi_none["badge_style"] == "badge-offline"
    assert "15" not in kpi_none["value"]

    # Case B: Empty dict
    kpi_empty = format_volatility_kpi({})
    assert kpi_empty["value"] == "N/A"
    assert kpi_empty["is_available"] is False
    assert "15" not in kpi_empty["value"]

    # Case C: Explicitly None value
    kpi_val_none = format_volatility_kpi({"annualized_volatility": None})
    assert kpi_val_none["value"] == "N/A"
    assert kpi_val_none["is_available"] is False
    assert "15" not in kpi_val_none["value"]

    # Case D: Zero or negative invalid vol
    kpi_zero = format_volatility_kpi({"annualized_volatility": 0.0})
    assert kpi_zero["value"] == "N/A"
    assert kpi_zero["is_available"] is False

def test_actual_volatility_displayed_correctly():
    """Requirement 2: Actual calculated volatility is displayed accurately."""
    # Case A: Low volatility (8.5%)
    kpi_low = format_volatility_kpi({"annualized_volatility": 0.085})
    assert kpi_low["value"] == "8.5%"
    assert "Low Volatility Regime" in kpi_low["delta"]
    assert kpi_low["is_available"] is True
    assert kpi_low["delta_type"] == "positive"

    # Case B: Moderate volatility (16.4%)
    kpi_mod = format_volatility_kpi({"annualized_volatility": 0.164})
    assert kpi_mod["value"] == "16.4%"
    assert "Moderate Volatility Regime" in kpi_mod["delta"]
    assert kpi_mod["is_available"] is True
    assert kpi_mod["delta_type"] == "negative"

    # Case C: Elevated volatility (24.8%)
    kpi_high = format_volatility_kpi({"annualized_volatility": 0.248})
    assert kpi_high["value"] == "24.8%"
    assert "Elevated Volatility Regime" in kpi_high["delta"]
    assert kpi_high["is_available"] is True

def test_market_mover_labels_tracked_universe():
    """Requirement 3: Market mover labels accurately describe the tracked universe."""
    header_meta = format_market_movers_header(tracked_count=5, universe_size=5, market="IN")
    assert header_meta["title"] == "Top Movers — Tracked Universe"
    assert "Tracked Universe: 5 of 5 active equities (IN)" in header_meta["caption"]

    # Test StockService.get_market_overview includes universe metadata
    overview = stock_service.get_market_overview("IN")
    assert "universe_size" in overview
    assert "tracked_count" in overview
    assert overview["universe_size"] > 0
    assert overview["tracked_count"] <= overview["universe_size"]
    assert isinstance(overview["gainers"], list)
    assert isinstance(overview["losers"], list)

def test_positive_sentiment_with_sample_data_displays_positive_and_sample():
    """Requirement 4: Positive sentiment with sample data displays Positive + Sample, not Live."""
    article = {
        "headline": "Company expands operating margin",
        "sentiment_label": "Positive",
        "is_sample": True
    }
    badges = get_sentiment_and_provenance_badges(article, global_is_sample=True)
    assert badges["sentiment_label"] == "Positive"
    assert badges["sentiment_badge_class"] == "badge-sentiment-pos"
    assert badges["provenance_label"] == "SAMPLE"
    assert badges["provenance_badge_class"] == "badge-sample"
    # Must NOT be badge-live
    assert badges["provenance_badge_class"] != "badge-live"
    assert badges["sentiment_badge_class"] != "badge-live"

def test_negative_sentiment_with_live_data_displays_negative_and_live():
    """Requirement 5: Negative sentiment with live data displays Negative + Live, not Offline."""
    article = {
        "headline": "Regulatory scrutiny tightens over compliance",
        "sentiment_label": "Negative",
        "is_sample": False,
        "is_cached": False
    }
    badges = get_sentiment_and_provenance_badges(article, global_is_sample=False, global_is_cached=False)
    assert badges["sentiment_label"] == "Negative"
    assert badges["sentiment_badge_class"] == "badge-sentiment-neg"
    assert badges["provenance_label"] == "LIVE"
    assert badges["provenance_badge_class"] == "badge-live"
    # Must NOT be badge-offline
    assert badges["provenance_badge_class"] != "badge-offline"
    assert badges["sentiment_badge_class"] != "badge-offline"

def test_user_id_dynamically_retrieved_and_passed():
    """Requirement 6: User ID is dynamically retrieved and passed to portfolio/watchlist queries."""
    default_user = Repository.get_or_create_default_user()
    assert default_user.id is not None
    user_id = default_user.id

    # Verify Repository accepts dynamic user_id
    portfolios = Repository.get_paper_portfolios(user_id=user_id, market="IN")
    assert isinstance(portfolios, list)
    assert len(portfolios) >= 1
    assert portfolios[0]["name"] is not None

    # Verify PortfolioService.get_paper_portfolio_overview accepts user_id
    pid = portfolios[0]["id"]
    overview = portfolio_service.get_paper_portfolio_overview(portfolio_id=pid, user_id=user_id)
    assert "total_value" in overview
    assert "cash" in overview
    assert overview["portfolio"]["id"] == pid

    # Verify watchlists accept user_id
    watchlists = Repository.get_watchlists(user_id=user_id, market="IN")
    assert isinstance(watchlists, list)
    assert len(watchlists) >= 1

def test_empty_watchlists_and_empty_news_handled_safely():
    """Requirement 7: Empty watchlists and empty news are handled safely without exceptions."""
    # Test query with non-existent user returns empty list safely
    empty_wl = Repository.get_watchlists(user_id=999999, market="IN")
    assert empty_wl == []

    # Test sentiment formatting with empty list
    from app.ml.sentiment_analyzer import sentiment_analyzer
    empty_res = sentiment_analyzer.analyze_batch([])
    assert empty_res == []

    # Test format volatility with invalid non-dict
    bad_vol = format_volatility_kpi("invalid_string")
    assert bad_vol["value"] == "N/A"
    assert bad_vol["is_available"] is False
