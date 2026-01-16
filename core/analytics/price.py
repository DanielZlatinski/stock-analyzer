import math

import pandas as pd

from core.analysis_models import PriceAnalytics


ROLLING_WINDOWS = {
    "1w": 5,
    "1m": 21,
    "3m": 63,
    "1y": 252,
}


def build_price_analytics(price_history, benchmark_history=None):
    if not price_history:
        return PriceAnalytics(
            total_return=None,
            annualized_volatility=None,
            max_drawdown=None,
            beta=None,
            correlation=None,
            rolling_returns={key: None for key in ROLLING_WINDOWS},
        )

    df = pd.DataFrame([point.__dict__ for point in price_history])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    returns = df["close"].pct_change().dropna()

    total_return = (df["close"].iloc[-1] / df["close"].iloc[0]) - 1
    annualized_volatility = (
        returns.std() * math.sqrt(252) if not returns.empty else None
    )
    drawdown = (df["close"] / df["close"].cummax()) - 1
    max_drawdown = drawdown.min() if not drawdown.empty else None

    rolling_returns = {}
    for horizon, window in ROLLING_WINDOWS.items():
        if len(df) > window:
            rolling_returns[horizon] = (df["close"].iloc[-1] / df["close"].iloc[-window - 1]) - 1
        else:
            rolling_returns[horizon] = None

    beta = None
    correlation = None
    if benchmark_history:
        bench_df = pd.DataFrame([point.__dict__ for point in benchmark_history])
        bench_df["date"] = pd.to_datetime(bench_df["date"])
        bench_df = bench_df.set_index("date").sort_index()
        combined = pd.concat(
            [df["close"].pct_change(), bench_df["close"].pct_change()],
            axis=1,
            join="inner",
        ).dropna()
        if len(combined.columns) == 2 and not combined.empty:
            cov = combined.cov().iloc[0, 1]
            var = combined.iloc[:, 1].var()
            beta = cov / var if var != 0 else None
            correlation = combined.corr().iloc[0, 1]

    return PriceAnalytics(
        total_return=total_return,
        annualized_volatility=annualized_volatility,
        max_drawdown=max_drawdown,
        beta=beta,
        correlation=correlation,
        rolling_returns=rolling_returns,
    )
