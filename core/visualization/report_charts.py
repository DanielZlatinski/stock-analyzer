import base64

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    HAS_PLOTLY = True
except ImportError:
    go = None
    pio = None
    HAS_PLOTLY = False


def _fig_to_base64(fig):
    if not HAS_PLOTLY:
        return None
    fig.update_layout(template="plotly_dark", height=420, margin=dict(l=40, r=20, t=40, b=40))
    image_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(image_bytes).decode("utf-8")


def price_chart(price_history):
    if not HAS_PLOTLY:
        return None
    if not price_history:
        return None
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=[p.date for p in price_history],
                open=[p.open for p in price_history],
                high=[p.high for p in price_history],
                low=[p.low for p in price_history],
                close=[p.close for p in price_history],
                name="Price",
            )
        ]
    )
    fig.update_layout(title="Price (Candlestick)")
    return _fig_to_base64(fig)


def relative_chart(price_history, benchmark_history):
    if not HAS_PLOTLY:
        return None
    if not price_history or not benchmark_history:
        return None
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
    return _fig_to_base64(fig)


def fundamentals_chart(time_series):
    if not HAS_PLOTLY:
        return None
    if not time_series:
        return None
    fig = go.Figure()
    for name, series in time_series.items():
        if not series:
            continue
        dates = list(sorted(series.keys()))
        fig.add_trace(go.Scatter(x=dates, y=[series[d] for d in dates], name=name))
    fig.update_layout(title="Fundamental Trends")
    return _fig_to_base64(fig)


def peers_chart(peer_metrics):
    if not HAS_PLOTLY:
        return None
    if not peer_metrics:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[item["ticker"] for item in peer_metrics],
            y=[item.get("pe_ratio") for item in peer_metrics],
            name="P/E",
        )
    )
    fig.update_layout(title="Peer P/E Comparison")
    return _fig_to_base64(fig)


def sentiment_chart(news_items):
    if not HAS_PLOTLY:
        return None
    if not news_items:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[item.published_at or item.title for item in news_items],
            y=list(range(1, len(news_items) + 1)),
            name="News Volume",
        )
    )
    fig.update_layout(title="News Volume (Recent)")
    return _fig_to_base64(fig)
