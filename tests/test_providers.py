"""
Unit Tests for Market Data Providers
"""
import pytest
from app.data_providers.offline_provider import OfflineDataProvider
from app.data_providers.factory import ProviderFactory

def test_offline_provider_indian_markets():
    provider = OfflineDataProvider()
    quote_res = provider.get_quote("RELIANCE.NS", market="IN")
    assert quote_res.is_success
    assert quote_res.is_sample is True
    assert quote_res.data.symbol == "RELIANCE.NS"
    assert quote_res.data.price > 0.0
    assert quote_res.data.currency == "INR"

    ohlcv_res = provider.get_historical_ohlcv("RELIANCE.NS", market="IN")
    assert ohlcv_res.is_success
    assert len(ohlcv_res.data) >= 100
    assert "Close" in ohlcv_res.data.columns

def test_offline_provider_us_markets():
    provider = OfflineDataProvider()
    quote_res = provider.get_quote("AAPL", market="US")
    assert quote_res.is_success
    assert quote_res.data.symbol == "AAPL"
    assert quote_res.data.currency == "USD"

    profile_res = provider.get_company_profile("AAPL", market="US")
    assert profile_res.is_success
    assert "Apple" in profile_res.data.name

def test_provider_factory_resolution():
    provider = ProviderFactory.get_provider(force_offline=True)
    assert isinstance(provider, OfflineDataProvider)
