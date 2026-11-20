"""
FinSight AI - Realistic Sample & Offline Market Data Generator
Generates multi-year historical OHLCV, financial statements, and news.
"""
import os
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PRICES_DIR = BASE_DIR / "data" / "sample_prices"
SAMPLE_FUNDAMENTALS_DIR = BASE_DIR / "data" / "sample_fundamentals"
SAMPLE_NEWS_DIR = BASE_DIR / "data" / "sample_news"

for d in (SAMPLE_PRICES_DIR, SAMPLE_FUNDAMENTALS_DIR, SAMPLE_NEWS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

# Symbol parameters
SYMBOLS_CONFIG = {
    # Indian Symbols (Prices in INR)
    "RELIANCE.NS": {"start_price": 2400.0, "end_price": 2950.0, "vol": 0.015, "market": "IN", "currency": "INR", "sector": "Energy"},
    "TCS.NS": {"start_price": 3400.0, "end_price": 4120.0, "vol": 0.013, "market": "IN", "currency": "INR", "sector": "Technology"},
    "INFY.NS": {"start_price": 1450.0, "end_price": 1820.0, "vol": 0.016, "market": "IN", "currency": "INR", "sector": "Technology"},
    "HDFCBANK.NS": {"start_price": 1500.0, "end_price": 1680.0, "vol": 0.014, "market": "IN", "currency": "INR", "sector": "Financial Services"},
    "ICICIBANK.NS": {"start_price": 950.0, "end_price": 1260.0, "vol": 0.015, "market": "IN", "currency": "INR", "sector": "Financial Services"},
    "^NSEI": {"start_price": 19500.0, "end_price": 24800.0, "vol": 0.010, "market": "IN", "currency": "INR", "sector": "Index"},

    # US Symbols (Prices in USD)
    "AAPL": {"start_price": 175.0, "end_price": 228.0, "vol": 0.016, "market": "US", "currency": "USD", "sector": "Technology"},
    "MSFT": {"start_price": 330.0, "end_price": 445.0, "vol": 0.015, "market": "US", "currency": "USD", "sector": "Technology"},
    "GOOGL": {"start_price": 130.0, "end_price": 178.0, "vol": 0.017, "market": "US", "currency": "USD", "sector": "Communication Services"},
    "NVDA": {"start_price": 45.0, "end_price": 128.0, "vol": 0.028, "market": "US", "currency": "USD", "sector": "Technology"},
    "AMZN": {"start_price": 135.0, "end_price": 192.0, "vol": 0.019, "market": "US", "currency": "USD", "sector": "Consumer Cyclical"},
    "SPY": {"start_price": 430.0, "end_price": 560.0, "vol": 0.011, "market": "US", "currency": "USD", "sector": "Index"},
}

def generate_ohlcv(symbol, cfg, num_days=500):
    """Generates realistic daily OHLCV dataframe over business days."""
    end_date = datetime.now()
    dates = pd.bdate_range(end=end_date, periods=num_days)

    start_p = cfg["start_price"]
    end_p = cfg["end_price"]
    daily_vol = cfg["vol"]

    # Geometric Brownian Motion with drift
    drift = (math.log(end_p / start_p)) / num_days
    returns = np.random.normal(loc=drift, scale=daily_vol, size=num_days)

    prices = [start_p]
    for r in returns[:-1]:
        prices.append(prices[-1] * math.exp(r))

    rows = []
    for d, p in zip(dates, prices):
        day_range = p * daily_vol * np.random.uniform(0.8, 1.8)
        open_p = p + np.random.uniform(-day_range * 0.3, day_range * 0.3)
        close_p = p + np.random.uniform(-day_range * 0.4, day_range * 0.4)
        high_p = max(open_p, close_p) + np.random.uniform(0.1, 0.6) * day_range
        low_p = min(open_p, close_p) - np.random.uniform(0.1, 0.6) * day_range
        
        # Base volume
        base_vol = 2_000_000 if cfg["market"] == "IN" else 25_000_000
        vol = int(base_vol * np.random.lognormal(mean=0, sigma=0.4))

        rows.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Open": round(open_p, 2),
            "High": round(high_p, 2),
            "Low": round(low_p, 2),
            "Close": round(close_p, 2),
            "Adj Close": round(close_p, 2),
            "Volume": vol
        })

    df = pd.DataFrame(rows)
    # Save CSV
    safe_sym = symbol.replace("^", "IDX_").replace(".", "_")
    csv_path = SAMPLE_PRICES_DIR / f"{safe_sym}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} rows for {symbol} -> {csv_path.name}")

def generate_fundamentals():
    """Generates financial metrics, balance sheet, and ratios for symbols."""
    fundamentals_data = {
        "RELIANCE.NS": {
            "pe_ratio": 26.4, "pb_ratio": 2.1, "ps_ratio": 2.2,
            "debt_to_equity": 0.42, "roe": 0.098, "roa": 0.051, "net_margin": 0.078,
            "revenue": 9850000000000, "net_income": 740000000000, "market_cap": 20100000000000,
            "dividend_yield": 0.0035, "currency": "INR", "market": "IN"
        },
        "TCS.NS": {
            "pe_ratio": 32.1, "pb_ratio": 14.2, "ps_ratio": 6.1,
            "debt_to_equity": 0.08, "roe": 0.495, "roa": 0.312, "net_margin": 0.192,
            "revenue": 2450000000000, "net_income": 465000000000, "market_cap": 15000000000000,
            "dividend_yield": 0.0135, "currency": "INR", "market": "IN"
        },
        "INFY.NS": {
            "pe_ratio": 28.5, "pb_ratio": 8.7, "ps_ratio": 4.8,
            "debt_to_equity": 0.11, "roe": 0.318, "roa": 0.205, "net_margin": 0.171,
            "revenue": 1550000000000, "net_income": 265000000000, "market_cap": 7500000000000,
            "dividend_yield": 0.0210, "currency": "INR", "market": "IN"
        },
        "HDFCBANK.NS": {
            "pe_ratio": 18.8, "pb_ratio": 2.6, "ps_ratio": 3.9,
            "debt_to_equity": 1.45, "roe": 0.162, "roa": 0.019, "net_margin": 0.224,
            "revenue": 2100000000000, "net_income": 640000000000, "market_cap": 12800000000000,
            "dividend_yield": 0.0115, "currency": "INR", "market": "IN"
        },
        "AAPL": {
            "pe_ratio": 33.4, "pb_ratio": 48.2, "ps_ratio": 8.9,
            "debt_to_equity": 1.52, "roe": 1.45, "roa": 0.285, "net_margin": 0.262,
            "revenue": 385000000000, "net_income": 101000000000, "market_cap": 3480000000000,
            "dividend_yield": 0.0045, "currency": "USD", "market": "US"
        },
        "MSFT": {
            "pe_ratio": 36.2, "pb_ratio": 12.8, "ps_ratio": 13.5,
            "debt_to_equity": 0.41, "roe": 0.384, "roa": 0.178, "net_margin": 0.354,
            "revenue": 245000000000, "net_income": 88000000000, "market_cap": 3310000000000,
            "dividend_yield": 0.0072, "currency": "USD", "market": "US"
        },
        "NVDA": {
            "pe_ratio": 54.8, "pb_ratio": 38.6, "ps_ratio": 28.2,
            "debt_to_equity": 0.18, "roe": 1.15, "roa": 0.62, "net_margin": 0.551,
            "revenue": 96000000000, "net_income": 53000000000, "market_cap": 3150000000000,
            "dividend_yield": 0.0003, "currency": "USD", "market": "US"
        },
    }

    with open(SAMPLE_FUNDAMENTALS_DIR / "fundamentals.json", "w") as f:
        json.dump(fundamentals_data, f, indent=2)
    print("Saved fundamentals.json")

def generate_news():
    """Generates sample financial news headlines with symbols and timestamps."""
    now = datetime.now()
    news_items = [
        # Indian Market News
        {"headline": "Reliance Industries expands retail footprint with 50 new tech hubs across tier-2 cities", "symbol": "RELIANCE.NS", "market": "IN", "source": "Mint Financial", "days_ago": 1, "sentiment": "Positive"},
        {"headline": "TCS signs $1.2B digital transformation deal with European logistics giant", "symbol": "TCS.NS", "market": "IN", "source": "Economic Times", "days_ago": 2, "sentiment": "Positive"},
        {"headline": "Infosys raises full-year revenue growth forecast to 4.5% amidst strong cloud demand", "symbol": "INFY.NS", "market": "IN", "source": "Business Standard", "days_ago": 3, "sentiment": "Positive"},
        {"headline": "HDFC Bank deposit growth outpaces credit expansion in latest quarterly update", "symbol": "HDFCBANK.NS", "market": "IN", "source": "MoneyControl", "days_ago": 4, "sentiment": "Positive"},
        {"headline": "RBI keeps repo rate unchanged at 6.50% citing persistent food inflation concerns", "symbol": "^NSEI", "market": "IN", "source": "Financial Express", "days_ago": 5, "sentiment": "Neutral"},
        {"headline": "Foreign portfolio investors pull ₹4,200 crore from Indian equities amid valuation caution", "symbol": "^NSEI", "market": "IN", "source": "LiveMint", "days_ago": 6, "sentiment": "Negative"},
        {"headline": "ICICI Bank reports 17% jump in quarterly net profit driven by lower loan loss provisions", "symbol": "ICICIBANK.NS", "market": "IN", "source": "CNBC-TV18", "days_ago": 7, "sentiment": "Positive"},
        {"headline": "Tech Mahindra and TCS face client spending delays in European manufacturing contracts", "symbol": "TCS.NS", "market": "IN", "source": "Economic Times", "days_ago": 9, "sentiment": "Negative"},

        # US Market News
        {"headline": "NVIDIA unveils next-generation Blackwell Ultra AI server architecture with 4x inference throughput", "symbol": "NVDA", "market": "US", "source": "Bloomberg", "days_ago": 1, "sentiment": "Positive"},
        {"headline": "Apple integrates upgraded generative AI models across iOS suite with privacy-first silicon", "symbol": "AAPL", "market": "US", "source": "Wall Street Journal", "days_ago": 2, "sentiment": "Positive"},
        {"headline": "Microsoft Azure cloud revenue accelerates 29% YoY powered by enterprise Copilot adoption", "symbol": "MSFT", "market": "US", "source": "Reuters", "days_ago": 3, "sentiment": "Positive"},
        {"headline": "Alphabet faces renewed antitrust inquiry over digital advertising technology practices", "symbol": "GOOGL", "market": "US", "source": "Financial Times", "days_ago": 4, "sentiment": "Negative"},
        {"headline": "Federal Reserve signals gradual easing cycle as core PCE inflation cools toward 2.6%", "symbol": "SPY", "market": "US", "source": "CNBC", "days_ago": 5, "sentiment": "Positive"},
        {"headline": "Amazon Web Services announces multi-billion dollar capital expenditure expansion in datacenters", "symbol": "AMZN", "market": "US", "source": "Barron's", "days_ago": 6, "sentiment": "Positive"},
        {"headline": "Consumer spending cools in retail sector while credit card delinquencies tick higher", "symbol": "SPY", "market": "US", "source": "MarketWatch", "days_ago": 8, "sentiment": "Negative"},
        {"headline": "Semiconductor equipment suppliers report chip lead times normalize across automotive lines", "symbol": "NVDA", "market": "US", "source": "Reuters", "days_ago": 10, "sentiment": "Neutral"},
    ]

    for item in news_items:
        pub_dt = now - timedelta(days=item["days_ago"], hours=random.randint(1, 12))
        item["published_at"] = pub_dt.strftime("%Y-%m-%d %H:%M:%S")

    with open(SAMPLE_NEWS_DIR / "news.json", "w") as f:
        json.dump(news_items, f, indent=2)
    print("Saved news.json")

def main():
    for sym, cfg in SYMBOLS_CONFIG.items():
        generate_ohlcv(sym, cfg)
    generate_fundamentals()
    generate_news()
    print("Sample data generation completed successfully!")

if __name__ == "__main__":
    main()
