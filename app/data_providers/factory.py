"""
FinSight AI - Market Data Provider Factory
Dynamically resolves data providers based on API key availability and configuration.
"""
from typing import Optional
from app.config import settings
from app.core.logger import logger
from app.data_providers.base import BaseMarketDataProvider
from app.data_providers.fmp_provider import FMPDataProvider
from app.data_providers.alpha_vantage_provider import AlphaVantageDataProvider
from app.data_providers.offline_provider import OfflineDataProvider

class ProviderFactory:
    _cached_provider: Optional[BaseMarketDataProvider] = None

    @classmethod
    def get_provider(cls, force_offline: bool = False) -> BaseMarketDataProvider:
        """Resolves the best available market data provider."""
        if force_offline or settings.OFFLINE_MODE:
            logger.info("Using Offline / Sample Data Provider (explicit or configured).")
            return OfflineDataProvider()

        if settings.FMP_API_KEY and settings.FMP_API_KEY != "your_fmp_api_key_here":
            logger.info("Using Financial Modeling Prep (FMP) Provider.")
            return FMPDataProvider(settings.FMP_API_KEY)

        if settings.ALPHA_VANTAGE_API_KEY and settings.ALPHA_VANTAGE_API_KEY != "your_alphavantage_api_key_here":
            logger.info("Using Alpha Vantage Provider.")
            return AlphaVantageDataProvider(settings.ALPHA_VANTAGE_API_KEY)

        # Fallback to realistic offline sample provider
        logger.info("No active API keys found; defaulting to high-fidelity Offline Sample Provider.")
        return OfflineDataProvider()

def get_market_data_provider() -> BaseMarketDataProvider:
    """Convenience helper to obtain active provider."""
    return ProviderFactory.get_provider()
