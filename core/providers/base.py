from abc import ABC, abstractmethod
from typing import Dict, List

from core.models import NewsItem, PricePoint, SocialPost, TickerContext


class DataProvider(ABC):
    @abstractmethod
    def get_ticker_context(self, ticker) -> TickerContext:
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, ticker, start, end, interval) -> List[PricePoint]:
        raise NotImplementedError

    @abstractmethod
    def get_fundamentals(self, ticker) -> Dict[str, float]:
        raise NotImplementedError

    @abstractmethod
    def get_financial_statements(self, ticker) -> Dict[str, Dict[str, Dict[str, float]]]:
        raise NotImplementedError

    @abstractmethod
    def get_news(self, ticker, start, end) -> List[NewsItem]:
        raise NotImplementedError

    @abstractmethod
    def get_social_posts(self, ticker, start, end) -> List[SocialPost]:
        raise NotImplementedError

    @abstractmethod
    def get_peers(self, ticker) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_sector_etf(self, ticker) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_earnings(self, ticker) -> dict:
        raise NotImplementedError
