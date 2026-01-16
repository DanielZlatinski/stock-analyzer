try:
    import plotly.graph_objects as go
    import plotly.io as pio
    HAS_PLOTLY = True
except ImportError:
    go = None
    pio = None
    HAS_PLOTLY = False


def _to_html(fig):
    if not HAS_PLOTLY:
        return _placeholder()
    fig.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=50, r=20, t=50, b=40),
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif", size=12),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def price_candlestick(price_history, technicals):
    if not HAS_PLOTLY:
        return _placeholder()
    if not price_history:
        return ""
    dates = [point.date for point in price_history]
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=dates,
                open=[p.open for p in price_history],
                high=[p.high for p in price_history],
                low=[p.low for p in price_history],
                close=[p.close for p in price_history],
                name="Price",
            )
        ]
    )
    if technicals.ma_20 is not None:
        fig.add_trace(go.Scatter(x=dates, y=_rolling(price_history, 20), mode="lines", name="MA 20"))
    if technicals.ma_50 is not None:
        fig.add_trace(go.Scatter(x=dates, y=_rolling(price_history, 50), mode="lines", name="MA 50"))
    if technicals.ma_200 is not None:
        fig.add_trace(go.Scatter(x=dates, y=_rolling(price_history, 200), mode="lines", name="MA 200"))
    fig.update_layout(title="Price (Candlestick)")
    return _to_html(fig)


def volume_chart(price_history):
    if not HAS_PLOTLY:
        return _placeholder()
    if not price_history:
        return ""
    fig = go.Figure(
        data=[
            go.Bar(
                x=[p.date for p in price_history],
                y=[p.volume for p in price_history],
                name="Volume",
            )
        ]
    )
    fig.update_layout(title="Volume")
    return _to_html(fig)


def relative_performance(price_history, benchmark_history):
    if not HAS_PLOTLY:
        return _placeholder()
    if not price_history or not benchmark_history:
        return ""
    base = price_history[0].close
    benchmark_base = benchmark_history[0].close
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[p.date for p in price_history],
            y=[(p.close / base) - 1 for p in price_history],
            name="Ticker",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[p.date for p in benchmark_history],
            y=[(p.close / benchmark_base) - 1 for p in benchmark_history],
            name="Benchmark",
        )
    )
    fig.update_layout(title="Relative Performance")
    return _to_html(fig)


def rolling_volatility(price_history):
    if not HAS_PLOTLY:
        return _placeholder()
    if not price_history:
        return ""
    vols = _rolling_vol(price_history, 20)
    fig = go.Figure(
        data=[go.Scatter(x=[p.date for p in price_history], y=vols, name="Volatility")]
    )
    fig.update_layout(title="Rolling Volatility (20d)")
    return _to_html(fig)


def fundamentals_trend(time_series, title):
    if not HAS_PLOTLY:
        return _placeholder()
    if not time_series:
        return ""
    fig = go.Figure()
    for series_name, series in time_series.items():
        if not series:
            continue
        dates = list(sorted(series.keys()))
        fig.add_trace(go.Scatter(x=dates, y=[series[d] for d in dates], name=series_name))
    fig.update_layout(title=title)
    return _to_html(fig)


def peer_comparison(peer_metrics, ticker=None):
    if not HAS_PLOTLY:
        return _placeholder()
    if not peer_metrics:
        return "<p class='no-data'>No peer data available.</p>"
    
    # Filter out peers with no P/E data
    valid_peers = [p for p in peer_metrics if p.get("pe_ratio") is not None]
    if not valid_peers:
        return "<p class='no-data'>No peer valuation data available.</p>"
    
    # Sort by P/E for better visualization
    valid_peers = sorted(valid_peers, key=lambda x: x.get("pe_ratio") or 0)
    
    tickers = [item["ticker"] for item in valid_peers]
    pe_values = [item.get("pe_ratio") for item in valid_peers]
    
    # Color the current ticker differently
    colors = ["#2563eb" if t == ticker else "#64748b" for t in tickers]
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=tickers,
            y=pe_values,
            name="P/E Ratio",
            marker_color=colors,
            text=[f"{v:.1f}" if v else "" for v in pe_values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Peer P/E Comparison",
        xaxis_title="Ticker",
        yaxis_title="P/E Ratio",
        showlegend=False,
    )
    return _to_html(fig)


def sentiment_chart(sentiment_summary):
    """Create a sentiment distribution chart."""
    if not HAS_PLOTLY:
        return _placeholder()
    if not sentiment_summary or not hasattr(sentiment_summary, 'positive_count'):
        return "<p class='no-data'>No sentiment data available.</p>"
    
    pos = sentiment_summary.positive_count
    neg = sentiment_summary.negative_count
    neu = sentiment_summary.neutral_count
    
    if pos == 0 and neg == 0 and neu == 0:
        return "<p class='no-data'>No news articles to analyze.</p>"
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Positive", "Neutral", "Negative"],
            y=[pos, neu, neg],
            marker_color=["#22c55e", "#94a3b8", "#ef4444"],
            text=[pos, neu, neg],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="News Sentiment Distribution",
        xaxis_title="Sentiment",
        yaxis_title="Number of Articles",
        showlegend=False,
    )
    return _to_html(fig)


def recommendation_waterfall(contributions, total_score):
    if not HAS_PLOTLY:
        return _placeholder()
    if not contributions:
        return ""
    labels = []
    values = []
    for key, value in contributions.items():
        labels.append(key.title())
        values.append(round(value, 2))
    labels.append("Total")
    values.append(round(total_score, 2))
    fig = go.Figure(
        go.Waterfall(
            name="Score",
            orientation="v",
            measure=["relative"] * (len(labels) - 1) + ["total"],
            x=labels,
            textposition="outside",
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        )
    )
    fig.update_layout(title="Recommendation Score Breakdown")
    return _to_html(fig)


def _rolling(price_history, window):
    closes = [p.close for p in price_history]
    values = []
    for idx in range(len(closes)):
        if idx + 1 < window:
            values.append(None)
        else:
            values.append(sum(closes[idx + 1 - window : idx + 1]) / window)
    return values


def _rolling_vol(price_history, window):
    closes = [p.close for p in price_history]
    returns = []
    for idx in range(1, len(closes)):
        returns.append((closes[idx] / closes[idx - 1]) - 1)
    vols = []
    for idx in range(len(returns)):
        if idx + 1 < window:
            vols.append(None)
        else:
            window_returns = returns[idx + 1 - window : idx + 1]
            mean = sum(window_returns) / window
            var = sum((r - mean) ** 2 for r in window_returns) / window
            vols.append((var**0.5) * (252**0.5))
    vols.insert(0, None)
    return vols


def _placeholder():
    return (
        "<div class=\"chart-placeholder\">"
        "Charts require the Plotly package. Install dependencies to enable charts."
        "</div>"
    )
