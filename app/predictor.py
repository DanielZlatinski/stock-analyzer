from app.analyzer import score_snapshot
from app.data_fetcher import get_stock_snapshot


def analyze_stock(ticker):
    snapshot = get_stock_snapshot(ticker)
    analysis = score_snapshot(snapshot)
    return {
        "snapshot": snapshot,
        "analysis": analysis,
    }
