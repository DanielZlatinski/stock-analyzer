import unittest

from core.analysis_models import (
    AnalysisPack,
    EarningsSummary,
    FundamentalAnalytics,
    PeerComparison,
    PriceAnalytics,
    SentimentSummary,
    TechnicalIndicators,
)
from core.scoring_service import ScoringService


class TestScoring(unittest.TestCase):
    def test_scoring_outputs_rating(self):
        analysis = AnalysisPack(
            price=PriceAnalytics(
                total_return=0.1,
                annualized_volatility=0.2,
                max_drawdown=-0.1,
                beta=1.1,
                correlation=0.8,
                rolling_returns={"1w": 0.01, "1m": 0.03, "3m": 0.05, "1y": 0.1},
            ),
            technicals=TechnicalIndicators(
                ma_20=100,
                ma_50=95,
                ma_200=80,
                rsi_14=55,
                macd=1.2,
                macd_signal=1.0,
                bollinger_upper=110,
                bollinger_lower=90,
                trend_by_horizon={"1m": "bullish", "3m": "bullish"},
            ),
            fundamentals=FundamentalAnalytics(
                valuation={"pe_ratio": 18, "forward_pe": 16, "price_to_book": 3, "market_cap": 100},
                profitability={"roe": 0.18, "operating_margins": 0.2, "profit_margins": 0.18},
                growth={"revenue_growth": 0.12, "earnings_growth": 0.15},
                balance_sheet={"debt_to_equity": 0.6},
                time_series={},
            ),
            risk={"beta": 1.1, "volatility": 0.2, "max_drawdown": -0.1},
            peers=PeerComparison(peer_metrics=[], percentile_ranks={}),
            sentiment=SentimentSummary(headline_score=1.0, headline_volume=5, social_volume=0),
            earnings=EarningsSummary(next_earnings_date=None, surprise_history=[]),
            recommendation=None,
        )
        rec = ScoringService().score(analysis, completeness_percent=80)
        self.assertIn(rec.rating, {"INVEST", "WATCH", "AVOID"})


if __name__ == "__main__":
    unittest.main()
