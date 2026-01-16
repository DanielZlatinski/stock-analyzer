import os


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")

DEFAULT_BENCHMARK = "SPY"

# Finnhub API key for news (free tier: 60 calls/min)
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "d5l1bthr01qt47mg4io0d5l1bthr01qt47mg4iog")

SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
    "Communication Services": "XLC",
}

HORIZON_MAP = {
    "1d": 1,
    "1w": 7,
    "1m": 30,
    "3m": 90,
    "1y": 365,
    "5y": 365 * 5,
}

TTL_SECONDS = {
    "context": 60 * 60 * 24,
    "prices": 60 * 10,
    "fundamentals": 60 * 60 * 24,
    "financials": 60 * 60 * 24,
    "news": 60 * 30,
    "social": 60 * 30,
    "peers": 60 * 60 * 24,
    "sector_etf": 60 * 60 * 24,
    "earnings": 60 * 60 * 6,
}
