import argparse
from datetime import datetime, timedelta

from core import (
    AnalysisService,
    DataService,
    DEFAULT_BENCHMARK,
    HORIZON_MAP,
    YFinanceProvider,
)
from core.logging import get_logger
from core.reporting import build_report


def resolve_dates(horizon):
    days = HORIZON_MAP.get(horizon)
    if days is None:
        raise ValueError(f"Unsupported horizon: {horizon}")
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def render_summary(snapshot, analysis):
    context = snapshot.context
    print("=== Data Summary ===")
    print(f"Ticker: {context.ticker}")
    print(f"Company: {context.company_name}")
    print(f"Sector: {context.sector or 'N/A'} | Industry: {context.industry or 'N/A'}")
    print(f"Exchange: {context.exchange or 'N/A'} | Currency: {context.currency or 'N/A'}")
    print(f"Benchmark: {context.benchmark or DEFAULT_BENCHMARK}")
    print(f"Peers: {', '.join(snapshot.peers) if snapshot.peers else 'N/A'}")
    print(f"Sector ETF: {snapshot.sector_etf}")
    print("")
    print("=== Data Freshness ===")
    for key, timestamp in snapshot.last_updated.items():
        value = timestamp.isoformat() if timestamp else "N/A"
        print(f"{key}: {value}")
    print("")
    print("=== Completeness ===")
    for name, section in snapshot.completeness.sections.items():
        print(f"{name}: {section.percent}% ({section.present}/{section.total})")
    print(f"Overall: {snapshot.completeness.overall_percent}%")
    print("")
    print("=== Core Analytics ===")
    print(f"Total Return: {analysis.price.total_return}")
    print(f"Volatility: {analysis.price.annualized_volatility}")
    print(f"Max Drawdown: {analysis.price.max_drawdown}")
    print(f"Beta vs Benchmark: {analysis.price.beta}")
    print(f"Correlation vs Benchmark: {analysis.price.correlation}")
    print(f"Trend (1m): {analysis.technicals.trend_by_horizon.get('1m')}")
    print(
        f"Sentiment (headlines): {analysis.sentiment.headline_score} "
        f"({analysis.sentiment.headline_volume} articles)"
    )
    print(f"Next Earnings Date: {analysis.earnings.next_earnings_date}")
    print("")
    print("=== Recommendation ===")
    print(f"Rating: {analysis.recommendation.rating}")
    print(f"Score: {analysis.recommendation.score}")
    print(f"Confidence: {analysis.recommendation.confidence}")


def main():
    parser = argparse.ArgumentParser(description="Research terminal CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a ticker")
    analyze_parser.add_argument("--ticker", required=True)
    analyze_parser.add_argument(
        "--horizon",
        default="1y",
        choices=sorted(HORIZON_MAP.keys()),
    )
    analyze_parser.add_argument("--interval", default="1d")
    analyze_parser.add_argument("--export", choices=["pdf", "html"])

    args = parser.parse_args()
    logger = get_logger()
    provider = YFinanceProvider()
    service = DataService(provider=provider, logger=logger)

    if args.command == "analyze":
        start, end = resolve_dates(args.horizon)
        snapshot = service.build_snapshot(
            ticker=args.ticker.upper(),
            start=start,
            end=end,
            interval=args.interval,
        )
        analysis = AnalysisService(service).analyze(snapshot, start, end, args.interval)
        render_summary(snapshot, analysis)
        if args.export:
            benchmark_prices = service.get_benchmark_prices(
                snapshot.context.benchmark, start, end, args.interval
            )
            path = build_report(
                snapshot=snapshot,
                analysis=analysis,
                benchmark_prices=benchmark_prices,
                output_dir="reports",
                export_format=args.export,
            )
            logger.info("Report written to %s", path)


if __name__ == "__main__":
    main()
