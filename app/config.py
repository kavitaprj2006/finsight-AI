"""
FinSight AI - Configuration Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

class Settings:
    # App & Environment
    APP_NAME: str = "FinSight AI"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Defaults
    DEFAULT_MARKET: str = os.getenv("DEFAULT_MARKET", "IN")
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "INR")
    
    # Data Provider Keys
    FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'finsight.db'}")
    
    # MLflow
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", str(BASE_DIR / "mlruns"))
    
    # Cache
    CACHE_DIR: Path = BASE_DIR / "data" / "cache"
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    OFFLINE_MODE: bool = os.getenv("OFFLINE_MODE", "false").lower() in ("true", "1", "yes")

    # Sample Data Directories
    SAMPLE_PRICES_DIR: Path = BASE_DIR / "data" / "sample_prices"
    SAMPLE_FUNDAMENTALS_DIR: Path = BASE_DIR / "data" / "sample_fundamentals"
    SAMPLE_NEWS_DIR: Path = BASE_DIR / "data" / "sample_news"

settings = Settings()
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
