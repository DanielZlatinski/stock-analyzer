import pandas as pd

from core.analysis_models import TechnicalIndicators


TREND_WINDOWS = {
    "1d": 1,
    "1w": 5,
    "1m": 21,
    "3m": 63,
    "1y": 252,
    "5y": 252 * 5,
}


def _rsi(series, window=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _trend_label(change):
    if change is None:
        return "neutral"
    if change > 0.05:
        return "bullish"
    if change < -0.05:
        return "bearish"
    return "neutral"


def build_technical_indicators(price_history):
    if not price_history:
        return TechnicalIndicators(
            ma_20=None,
            ma_50=None,
            ma_200=None,
            rsi_14=None,
            macd=None,
            macd_signal=None,
            bollinger_upper=None,
            bollinger_lower=None,
            trend_by_horizon={key: "neutral" for key in TREND_WINDOWS},
        )

    df = pd.DataFrame([point.__dict__ for point in price_history])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    close = df["close"]

    ma_20 = close.rolling(window=20).mean().iloc[-1] if len(close) >= 20 else None
    ma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
    ma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None

    rsi_series = _rsi(close)
    rsi_14 = rsi_series.iloc[-1] if not rsi_series.empty else None

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd_series = ema_12 - ema_26
    macd = macd_series.iloc[-1] if not macd_series.empty else None
    signal_series = macd_series.ewm(span=9, adjust=False).mean()
    macd_signal = signal_series.iloc[-1] if not signal_series.empty else None

    rolling_mean = close.rolling(window=20).mean()
    rolling_std = close.rolling(window=20).std()
    bollinger_upper = (
        (rolling_mean + (2 * rolling_std)).iloc[-1]
        if len(close) >= 20
        else None
    )
    bollinger_lower = (
        (rolling_mean - (2 * rolling_std)).iloc[-1]
        if len(close) >= 20
        else None
    )

    trend_by_horizon = {}
    for horizon, window in TREND_WINDOWS.items():
        if len(close) > window:
            change = (close.iloc[-1] / close.iloc[-window - 1]) - 1
        else:
            change = None
        trend_by_horizon[horizon] = _trend_label(change)

    return TechnicalIndicators(
        ma_20=ma_20,
        ma_50=ma_50,
        ma_200=ma_200,
        rsi_14=rsi_14,
        macd=macd,
        macd_signal=macd_signal,
        bollinger_upper=bollinger_upper,
        bollinger_lower=bollinger_lower,
        trend_by_horizon=trend_by_horizon,
    )
