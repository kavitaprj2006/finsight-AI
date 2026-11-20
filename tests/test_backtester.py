"""
Unit Tests for Historical Strategy Backtester
"""
import pytest
import numpy as np
import pandas as pd
from app.analytics.backtester import HistoricalBacktester

@pytest.fixture
def multi_asset_prices_backtest():
    """Generates 200 days of price data across 3 assets + benchmark."""
    np.random.seed(42)
    dates = pd.bdate_range(end=pd.Timestamp.now(), periods=200)
    
    ret_a = np.random.normal(0.0008, 0.015, 200)
    ret_b = np.random.normal(0.0005, 0.010, 200)
    ret_c = np.random.normal(0.0004, 0.008, 200)
    ret_bench = np.random.normal(0.0005, 0.010, 200)

    p_a = 100.0 * np.cumprod(1.0 + ret_a)
    p_b = 50.0 * np.cumprod(1.0 + ret_b)
    p_c = 200.0 * np.cumprod(1.0 + ret_c)
    p_bench = pd.Series(1000.0 * np.cumprod(1.0 + ret_bench), index=dates, name="Benchmark")

    df = pd.DataFrame({"A": p_a, "B": p_b, "C": p_c}, index=dates)
    return df, p_bench

def test_backtester_execution(multi_asset_prices_backtest):
    prices_df, bench = multi_asset_prices_backtest
    bt = HistoricalBacktester(
        prices_df=prices_df,
        benchmark_prices=bench,
        initial_capital=100000.0,
        rebalance_interval_days=21,
        transaction_cost_pct=0.001,
        slippage_pct=0.0005,
        lookback_window_days=60
    )

    res = bt.run(strategy="EQUAL_WEIGHT", max_weight=0.50)
    assert "final_value" in res
    assert "total_return_pct" in res
    assert "cagr" in res
    assert "volatility" in res
    assert "sharpe_ratio" in res
    assert "max_drawdown" in res
    assert "equity_curve" in res
    assert "rebalances" in res
    assert len(res["rebalances"]) > 0
    assert res["final_value"] > 0.0
