import unittest

from core.analytics.price import build_price_analytics
from core.models import PricePoint


class TestPriceAnalytics(unittest.TestCase):
    def test_basic_price_metrics(self):
        prices = [
            PricePoint(date="2024-01-01", open=10, high=10, low=10, close=10, volume=100),
            PricePoint(date="2024-01-02", open=11, high=11, low=11, close=11, volume=100),
            PricePoint(date="2024-01-03", open=12, high=12, low=12, close=12, volume=100),
        ]
        analytics = build_price_analytics(prices)
        self.assertAlmostEqual(analytics.total_return, 0.2)
        self.assertIsNotNone(analytics.max_drawdown)


if __name__ == "__main__":
    unittest.main()
