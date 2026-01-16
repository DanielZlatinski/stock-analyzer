import math

import yfinance as yf

from app.utils import safe_float


def get_stock_snapshot(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    snapshot = {
        "name": info.get("shortName") or info.get("longName") or ticker,
        "price": safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
        "market_cap": safe_float(info.get("marketCap")),
        "pe_ratio": safe_float(info.get("trailingPE")),
        "forward_pe": safe_float(info.get("forwardPE")),
        "price_to_book": safe_float(info.get("priceToBook")),
        "roe": safe_float(info.get("returnOnEquity")),
        "debt_to_equity": safe_float(info.get("debtToEquity")),
        "revenue_growth": safe_float(info.get("revenueGrowth")),
        "eps_growth": safe_float(info.get("earningsGrowth")),
        "dividend_yield": safe_float(info.get("dividendYield")),
        "beta": safe_float(info.get("beta")),
        "fifty_two_week_high": safe_float(info.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": safe_float(info.get("fiftyTwoWeekLow")),
        "currency": info.get("currency") or "USD",
    }

    history = stock.history(period="6mo", interval="1d")
    if not history.empty:
        snapshot["history"] = [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "close": float(row["Close"]),
            }
            for idx, row in history.iterrows()
            if not math.isnan(row["Close"])
        ]
    else:
        snapshot["history"] = []

    return snapshot
