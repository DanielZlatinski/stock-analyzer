import traceback
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request

from core import AnalysisService, DataService, HORIZON_MAP, YFinanceProvider
from core.logging import get_logger
from core.visualization.plotly_charts import (
    fundamentals_trend,
    peer_comparison,
    price_candlestick,
    relative_performance,
    recommendation_waterfall,
    rolling_volatility,
    sentiment_chart,
    volume_chart,
)
from core.visualization.chart_explanations import build_chart_insights


bp = Blueprint("routes", __name__)
logger = get_logger(__name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            ticker = request.form.get("ticker", "").strip().upper()
            horizon = request.form.get("horizon", "1y")
            interval = request.form.get("interval", "1d")
            if not ticker:
                return render_template("index.html", error="Please enter a ticker.")

            logger.info(f"Processing request for ticker: {ticker}, horizon: {horizon}, interval: {interval}")

            days = HORIZON_MAP.get(horizon, 365)
            end = datetime.utcnow()
            start = end - timedelta(days=days)
            start_str = start.strftime("%Y-%m-%d")
            end_str = end.strftime("%Y-%m-%d")

            logger.info(f"Fetching data for {ticker} from {start_str} to {end_str}")
            provider = YFinanceProvider()
            service = DataService(provider=provider)
            snapshot = service.build_snapshot(ticker, start_str, end_str, interval)
            
            logger.info(f"Running analysis for {ticker}")
            analysis = AnalysisService(service).analyze(snapshot, start_str, end_str, interval)

            logger.info(f"Fetching benchmark prices")
            benchmark_prices = service.get_benchmark_prices(
                snapshot.context.benchmark, start_str, end_str, interval
            )

            logger.info(f"Generating charts for {ticker}")
            charts = {
                "price": price_candlestick(snapshot.price_history, analysis.technicals),
                "volume": volume_chart(snapshot.price_history),
                "relative": relative_performance(snapshot.price_history, benchmark_prices),
                "volatility": rolling_volatility(snapshot.price_history),
                "fundamentals": fundamentals_trend(
                    analysis.fundamentals.time_series, "Fundamental Trends"
                ),
                "peers": peer_comparison(analysis.peers.peer_metrics, ticker),
                "sentiment": sentiment_chart(analysis.sentiment),
                "recommendation": recommendation_waterfall(
                    analysis.recommendation.contributions,
                    analysis.recommendation.score,
                ),
            }
            
            logger.info(f"Building chart insights")
            chart_insights = build_chart_insights(
                ticker=ticker,
                snapshot=snapshot,
                analysis=analysis,
                benchmark_prices=benchmark_prices,
            )

            logger.info(f"Rendering template for {ticker}")
            return render_template(
                "index.html",
                ticker=ticker,
                horizon=horizon,
                interval=interval,
                snapshot=snapshot,
                analysis=analysis,
                charts=charts,
                chart_insights=chart_insights,
            )
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            
            # User-friendly error messages
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
                error_msg = f"Yahoo Finance is rate-limiting requests. Please wait a minute and try again. (This happens when too many requests are made from the same server.)"
            elif "unable to fetch" in error_str:
                error_msg = f"Unable to fetch data for {ticker}. Yahoo Finance may be temporarily unavailable. Please try again in a few minutes."
            else:
                error_msg = f"Error processing {ticker}: {str(e)}"
            
            return render_template("index.html", error=error_msg, horizon=horizon, interval=interval)

    return render_template("index.html", horizon="1y", interval="1d")


@bp.route("/test")
def test():
    """Simple test endpoint to verify the app is working"""
    try:
        import sys
        import os
        info = {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "project_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        }
        # Test imports
        try:
            from core import DataService, YFinanceProvider
            info["core_imports"] = "OK"
        except Exception as e:
            info["core_imports"] = f"FAILED: {str(e)}"
        
        try:
            import yfinance
            info["yfinance"] = "OK"
        except Exception as e:
            info["yfinance"] = f"FAILED: {str(e)}"
        
        try:
            import plotly
            info["plotly"] = "OK"
        except Exception as e:
            info["plotly"] = f"FAILED: {str(e)}"
        
        return f"<pre>{info}</pre>"
    except Exception as e:
        return f"<pre>Error: {str(e)}\n{traceback.format_exc()}</pre>"
