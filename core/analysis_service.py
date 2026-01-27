from core.analysis_models import AnalysisPack
from core.analytics import (
    build_earnings_summary,
    build_fundamental_analytics,
    build_peer_comparison,
    build_price_analytics,
    build_sentiment_summary,
    build_technical_indicators,
)
from core.scoring_service import ScoringService


class AnalysisService:
    def __init__(self, data_service):
        self.data_service = data_service

    def analyze(self, snapshot, start, end, interval):
        benchmark_prices = self.data_service.get_benchmark_prices(
            snapshot.context.benchmark, start, end, interval
        )
        price = build_price_analytics(snapshot.price_history, benchmark_prices)
        technicals = build_technical_indicators(snapshot.price_history)
        fundamentals = build_fundamental_analytics(
            snapshot.fundamentals, snapshot.financial_statements
        )
        peer_fundamentals = self.data_service.get_peer_fundamentals(snapshot.peers)
        peers = build_peer_comparison(
            snapshot.context.ticker, snapshot.fundamentals, peer_fundamentals
        )
        sentiment = build_sentiment_summary(snapshot.news, snapshot.social_posts)
        earnings = build_earnings_summary(snapshot.earnings)
        risk = {
            "beta": price.beta,
            "volatility": price.annualized_volatility,
            "max_drawdown": price.max_drawdown,
        }
        
        # Get quote type and sector from context for proper scoring
        quote_type = getattr(snapshot.context, 'quote_type', None)
        sector = snapshot.context.sector
        
        recommendation = ScoringService().score(
            analysis=AnalysisPack(
                price=price,
                technicals=technicals,
                fundamentals=fundamentals,
                risk=risk,
                peers=peers,
                sentiment=sentiment,
                earnings=earnings,
                recommendation=None,
            ),
            completeness_percent=snapshot.completeness.overall_percent,
            quote_type=quote_type,
            sector=sector,
        )

        return AnalysisPack(
            price=price,
            technicals=technicals,
            fundamentals=fundamentals,
            risk=risk,
            peers=peers,
            sentiment=sentiment,
            earnings=earnings,
            recommendation=recommendation,
        )
