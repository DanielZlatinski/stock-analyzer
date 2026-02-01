from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PriceAnalytics:
    total_return: Optional[float]
    annualized_volatility: Optional[float]
    max_drawdown: Optional[float]
    beta: Optional[float]
    correlation: Optional[float]
    rolling_returns: Dict[str, Optional[float]]
    current: Optional[float] = None  # Current price for timing calculations


@dataclass
class TechnicalIndicators:
    ma_20: Optional[float]
    ma_50: Optional[float]
    ma_200: Optional[float]
    rsi_14: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_lower: Optional[float]
    trend_by_horizon: Dict[str, str]


@dataclass
class FundamentalAnalytics:
    valuation: Dict[str, object]
    profitability: Dict[str, Optional[float]]
    growth: Dict[str, Optional[float]]
    balance_sheet: Dict[str, Optional[float]]
    time_series: Dict[str, Dict[str, float]]
    dividend: Dict[str, Optional[float]] = None
    per_share: Dict[str, Optional[float]] = None


@dataclass
class PeerComparison:
    peer_metrics: List[Dict[str, Optional[float]]]
    percentile_ranks: Dict[str, Optional[float]]


@dataclass
class SentimentSummary:
    headline_score: Optional[float]
    headline_volume: int
    social_volume: int
    scored_items: List[Dict] = None
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    overall_sentiment: str = "No Data"
    sentiment_description: str = ""


@dataclass
class EarningsSummary:
    next_earnings_date: Optional[str]
    surprise_history: List[Dict[str, Optional[float]]]


@dataclass
class AnalysisPack:
    price: PriceAnalytics
    technicals: TechnicalIndicators
    fundamentals: FundamentalAnalytics
    risk: Dict[str, Optional[float]]
    peers: PeerComparison
    sentiment: SentimentSummary
    earnings: EarningsSummary
    recommendation: Optional["Recommendation"]


@dataclass
class Recommendation:
    rating: str
    score: float
    confidence: str
    contributions: Dict[str, float]
    positives: List[str]
    risks: List[str]
    triggers: List[str]
    rating_description: str = ""
    factor_details: Dict[str, Dict] = None
    factor_scores: Dict[str, float] = None
    timing_signal: str = "Fair"  # Excellent, Good, Fair, Poor
    timing_score: float = 50.0
    timing_description: str = ""
    is_etf: bool = False