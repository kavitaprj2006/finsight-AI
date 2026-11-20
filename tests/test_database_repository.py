"""
Unit Tests for Database Operations and Repository Logic
"""
import pytest
from app.database.repository import Repository

def test_default_user_and_watchlists():
    user = Repository.get_or_create_default_user()
    assert user.id is not None
    assert user.username == "default_trader"

    wls = Repository.get_watchlists(user_id=user.id, market="IN")
    assert len(wls) >= 1
    assert "RELIANCE.NS" in wls[0]["symbols"]

def test_add_remove_watchlist_item():
    user = Repository.get_or_create_default_user()
    wls = Repository.get_watchlists(user_id=user.id, market="IN")
    target_wl = wls[0]

    # Add item
    added = Repository.add_to_watchlist(user.id, target_wl["name"], "WIPRO.NS", market="IN")
    assert added is True

    # Re-adding should return False
    duplicate = Repository.add_to_watchlist(user.id, target_wl["name"], "WIPRO.NS", market="IN")
    assert duplicate is False

    # Remove item
    removed = Repository.remove_from_watchlist(user.id, target_wl["id"], "WIPRO.NS")
    assert removed is True

def test_paper_portfolio_transactions():
    user = Repository.get_or_create_default_user()
    pid = Repository.create_paper_portfolio(
        user_id=user.id,
        name="Test Regression Fund",
        market="IN",
        currency="INR",
        initial_cash=100000.0
    )
    assert pid is not None

    # Buy 10 shares of RELIANCE.NS at 2500
    Repository.record_transaction(pid, "RELIANCE.NS", "BUY", quantity=10, price=2500.0, cost=10.0)
    holdings = Repository.get_portfolio_holdings(pid)
    assert "RELIANCE.NS" in holdings
    assert holdings["RELIANCE.NS"]["quantity"] == 10.0
    assert pytest.approx(holdings["RELIANCE.NS"]["avg_cost"], abs=1.0) == 2501.0

    # Sell 5 shares at 2700
    Repository.record_transaction(pid, "RELIANCE.NS", "SELL", quantity=5, price=2700.0, cost=5.0)
    holdings_after = Repository.get_portfolio_holdings(pid)
    assert holdings_after["RELIANCE.NS"]["quantity"] == 5.0
    assert holdings_after["RELIANCE.NS"]["realized_pnl"] > 0.0

def test_alerts_lifecycle():
    user = Repository.get_or_create_default_user()
    alert_id = Repository.create_alert(user.id, "TCS.NS", "PRICE_ABOVE", threshold=4200.0, market="IN")
    assert alert_id is not None

    active_alerts = Repository.get_active_alerts(user.id)
    assert any(a["id"] == alert_id for a in active_alerts)

    # Record event
    Repository.record_alert_event(alert_id, "TCS.NS", 4210.0, 4200.0, "Target breached")
    events = Repository.get_alert_events(user.id)
    assert len(events) >= 1
    assert events[0]["symbol"] == "TCS.NS"

    # Delete alert
    deleted = Repository.delete_alert(alert_id)
    assert deleted is True
