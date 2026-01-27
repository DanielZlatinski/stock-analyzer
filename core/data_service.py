from datetime import datetime

from core.cache import get_cache
from core.config import TTL_SECONDS
from core.logging import get_logger
from core.models import DataQualityReport, DataSnapshot


class DataService:
    def __init__(self, provider, cache=None, logger=None):
        self.provider = provider
        self.cache = cache or get_cache()
        self.logger = logger or get_logger()

    def _cache_key(self, name, *parts):
        joined = "|".join(str(part) for part in parts)
        return f"{self.provider.__class__.__name__}:{name}:{joined}"

    def _fetch_cached(self, name, ttl, fetcher, *parts):
        key = self._cache_key(name, *parts)
        cached, stored_at = self.cache.get(key, ttl)
        if cached is not None:
            return cached, stored_at
        data = fetcher()
        stored_at = self.cache.set(key, data)
        return data, stored_at

    def build_snapshot(self, ticker, start, end, interval):
        completeness = DataQualityReport()
        last_updated = {}

        context, last_updated["context"] = self._fetch_cached(
            "context",
            TTL_SECONDS["context"],
            lambda: self.provider.get_ticker_context(ticker),
            ticker,
        )

        prices, last_updated["prices"] = self._fetch_cached(
            "prices",
            TTL_SECONDS["prices"],
            lambda: self.provider.get_price_history(ticker, start, end, interval),
            ticker,
            start,
            end,
            interval,
        )
        price_section = completeness.section("prices")
        price_section.add(bool(prices), "Price history missing or empty.")

        fundamentals, last_updated["fundamentals"] = self._fetch_cached(
            "fundamentals",
            TTL_SECONDS["fundamentals"],
            lambda: self.provider.get_fundamentals(ticker),
            ticker,
        )
        fundamentals_section = completeness.section("fundamentals")
        for key in ["market_cap", "pe_ratio", "roe", "debt_to_equity", "revenue_growth"]:
            fundamentals_section.add(
                fundamentals.get(key) is not None,
                f"Missing fundamentals field: {key}",
            )

        financials, last_updated["financials"] = self._fetch_cached(
            "financials",
            TTL_SECONDS["financials"],
            lambda: self.provider.get_financial_statements(ticker),
            ticker,
        )
        financials_section = completeness.section("financials")
        financials_section.add(bool(financials), "Financial statements missing.")

        news, last_updated["news"] = self._fetch_cached(
            "news",
            TTL_SECONDS["news"],
            lambda: self.provider.get_news(ticker, start, end),
            ticker,
            start,
            end,
        )
        news_section = completeness.section("news")
        news_section.add(bool(news), "No news items returned.")

        social, last_updated["social"] = self._fetch_cached(
            "social",
            TTL_SECONDS["social"],
            lambda: self.provider.get_social_posts(ticker, start, end),
            ticker,
            start,
            end,
        )
        social_section = completeness.section("social")
        social_section.add(bool(social), "No social posts returned.")

        peers, last_updated["peers"] = self._fetch_cached(
            "peers",
            TTL_SECONDS["peers"],
            lambda: self.provider.get_peers(ticker),
            ticker,
        )
        peers_section = completeness.section("peers")
        peers_section.add(bool(peers), "Peer list missing.")

        sector_etf, last_updated["sector_etf"] = self._fetch_cached(
            "sector_etf",
            TTL_SECONDS["sector_etf"],
            lambda: self.provider.get_sector_etf(ticker),
            ticker,
        )
        sector_section = completeness.section("sector_etf")
        sector_section.add(bool(sector_etf), "Sector ETF missing.")

        earnings, last_updated["earnings"] = self._fetch_cached(
            "earnings",
            TTL_SECONDS["earnings"],
            lambda: self.provider.get_earnings(ticker),
            ticker,
        )
        earnings_section = completeness.section("earnings")
        earnings_section.add(
            bool(earnings.get("next_earnings_date")),
            "Next earnings date missing.",
        )

        self._log_warnings(completeness)

        return DataSnapshot(
            context=context,
            price_history=prices,
            fundamentals=fundamentals,
            financial_statements=financials,
            news=news,
            social_posts=social,
            peers=peers,
            sector_etf=sector_etf,
            earnings=earnings,
            last_updated=last_updated,
            completeness=completeness,
        )

    def get_peer_fundamentals(self, tickers, limit=5):
        results = {}
        for peer in tickers[:limit]:
            data, _stored_at = self._fetch_cached(
                "peer_fundamentals",
                TTL_SECONDS["fundamentals"],
                lambda peer=peer: self.provider.get_fundamentals(peer),
                peer,
            )
            results[peer] = data
        return results

    def get_benchmark_prices(self, benchmark, start, end, interval):
        prices, _stored_at = self._fetch_cached(
            "benchmark_prices",
            TTL_SECONDS["prices"],
            lambda: self.provider.get_price_history(benchmark, start, end, interval),
            benchmark,
            start,
            end,
            interval,
        )
        return prices

    def _log_warnings(self, completeness):
        for section in completeness.sections.values():
            for warning in section.warnings:
                self.logger.warning("%s: %s", section.name, warning)
