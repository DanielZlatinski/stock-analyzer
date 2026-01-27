from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TickerContext:
    ticker: str
    company_name: str
    sector: Optional[str]
    industry: Optional[str]
    exchange: Optional[str]
    currency: Optional[str]
    peers: List[str]
    benchmark: str
    quote_type: Optional[str] = None  # EQUITY, ETF, MUTUALFUND, INDEX, etc.


@dataclass
class PricePoint:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class NewsItem:
    title: str
    publisher: Optional[str]
    url: Optional[str]
    published_at: Optional[str]


@dataclass
class SocialPost:
    source: str
    title: str
    url: Optional[str]
    published_at: Optional[str]
    score: Optional[int]
    comments: Optional[int]


@dataclass
class CompletenessSection:
    name: str
    total: int = 0
    present: int = 0
    warnings: List[str] = field(default_factory=list)

    def add(self, present, warning=None):
        self.total += 1
        if present:
            self.present += 1
        elif warning:
            self.warnings.append(warning)

    @property
    def percent(self):
        if self.total == 0:
            return 0.0
        return round((self.present / self.total) * 100, 1)


@dataclass
class DataQualityReport:
    sections: Dict[str, CompletenessSection] = field(default_factory=dict)

    def section(self, name):
        if name not in self.sections:
            self.sections[name] = CompletenessSection(name=name)
        return self.sections[name]

    @property
    def overall_percent(self):
        totals = sum(section.total for section in self.sections.values())
        present = sum(section.present for section in self.sections.values())
        if totals == 0:
            return 0.0
        return round((present / totals) * 100, 1)


@dataclass
class DataSnapshot:
    context: TickerContext
    price_history: List[PricePoint]
    fundamentals: Dict[str, Optional[float]]
    financial_statements: Dict[str, Dict[str, Dict[str, float]]]
    news: List[NewsItem]
    social_posts: List[SocialPost]
    peers: List[str]
    sector_etf: str
    earnings: Dict[str, object]
    last_updated: Dict[str, Optional[datetime]]
    completeness: DataQualityReport
