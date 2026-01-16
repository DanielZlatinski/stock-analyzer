from datetime import datetime, timedelta

from flask import Blueprint, render_template, request

from core import AnalysisService, DataService, HORIZON_MAP, YFinanceProvider
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


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ticker = request.form.get("ticker", "").strip().upper()
        horizon = request.form.get("horizon", "1y")
        interval = request.form.get("interval", "1d")
        if not ticker:
            return render_template("index.html", error="Please enter a ticker.")

        days = HORIZON_MAP.get(horizon, 365)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        provider = YFinanceProvider()
        service = DataService(provider=provider)
        snapshot = service.build_snapshot(ticker, start_str, end_str, interval)
        analysis = AnalysisService(service).analyze(snapshot, start_str, end_str, interval)

        benchmark_prices = service.get_benchmark_prices(
            snapshot.context.benchmark, start_str, end_str, interval
        )

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
        chart_insights = build_chart_insights(
            ticker=ticker,
            snapshot=snapshot,
            analysis=analysis,
            benchmark_prices=benchmark_prices,
        )

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

    return render_template("index.html", horizon="1y", interval="1d")
