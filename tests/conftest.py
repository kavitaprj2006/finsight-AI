"""
Pytest Configuration and Shared Test Fixtures
"""
import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.connection import init_db
from app.database.repository import Repository

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initializes test database and seeds default records."""
    init_db()
    Repository.get_or_create_default_user()
    Repository.seed_stock_symbols()

@pytest.fixture
def sample_price_series():
    """Provides a synthetic 100-day price series with known positive trend."""
    np.random.seed(42)
    dates = pd.bdate_range(end=pd.Timestamp.now(), periods=100)
    returns = np.random.normal(loc=0.001, scale=0.015, size=100)
    prices = [100.0]
    for r in returns[:-1]:
        prices.append(prices[-1] * (1.0 + r))
    return pd.Series(prices, index=dates, name="Close")

@pytest.fixture
def sample_ohlcv_df():
    """Provides a synthetic 100-day OHLCV DataFrame."""
    np.random.seed(42)
    dates = pd.bdate_range(end=pd.Timestamp.now(), periods=100)
    rows = []
    price = 100.0
    for d in dates:
        ret = np.random.normal(loc=0.0005, scale=0.012)
        price *= (1.0 + ret)
        high = price * 1.01
        low = price * 0.99
        rows.append({
            "Date": d,
            "Open": price * 0.998,
            "High": high,
            "Low": low,
            "Close": price,
            "Adj Close": price,
            "Volume": 1000000
        })
    df = pd.DataFrame(rows)
    df.set_index("Date", inplace=True)
    return df
