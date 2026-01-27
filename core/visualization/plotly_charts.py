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


def indices_comparison(ticker_history, indices_data, ticker_symbol="Stock"):
    """
    Create a comparison chart showing relative performance vs major indices.
    
    Args:
        ticker_history: List of PricePoint for the stock
        indices_data: Dict of {index_name: List of PricePoint}
        ticker_symbol: Stock ticker symbol for legend
    """
    if not HAS_PLOTLY:
        return _placeholder()
    if not ticker_history:
        return "<p style='padding: 40px; text-align: center; color: #64748b;'>No price data available</p>"
    
    fig = go.Figure()
    
    # Calculate normalized returns for stock
    base = ticker_history[0].close
    stock_returns = [(p.close / base - 1) * 100 for p in ticker_history]
    dates = [p.date for p in ticker_history]
    
    # Add stock trace
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=stock_returns,
            name=ticker_symbol,
            line=dict(color="#2563eb", width=2.5),
        )
    )
    
    # Color palette for indices
    colors = {"S&P 500": "#10b981", "NASDAQ": "#8b5cf6", "DOW": "#f59e0b"}
    
    # Add index traces
    for index_name, index_history in indices_data.items():
        if index_history and len(index_history) > 0:
            index_base = index_history[0].close
            index_returns = [(p.close / index_base - 1) * 100 for p in index_history]
            index_dates = [p.date for p in index_history]
            
            fig.add_trace(
                go.Scatter(
                    x=index_dates,
                    y=index_returns,
                    name=index_name,
                    line=dict(color=colors.get(index_name, "#64748b"), width=1.5, dash="dot"),
                )
            )
    
    fig.update_layout(
        title=f"{ticker_symbol} vs Major Indices (% Change)",
        xaxis_title="Date",
        yaxis_title="Return (%)",
        yaxis_ticksuffix="%",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return _to_html(fig)


def sentiment_gauge(score, sentiment_label):
    """
    Create a sentiment gauge visualization.
    Score ranges from -100 (bearish) to +100 (bullish).
    """
    if not HAS_PLOTLY:
        return _placeholder()
    
    # Clamp score to valid range
    score = max(-100, min(100, score))
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Market Sentiment: {sentiment_label}", 'font': {'size': 16}},
        number={'suffix': "", 'font': {'size': 36}},
        gauge={
            'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "#64748b"},
            'bar': {'color': "#1e293b", 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
            'steps': [
                {'range': [-100, -30], 'color': '#ef4444'},  # Bearish - red
                {'range': [-30, -10], 'color': '#f97316'},   # Slightly bearish - orange
                {'range': [-10, 10], 'color': '#94a3b8'},    # Neutral - gray
                {'range': [10, 30], 'color': '#84cc16'},     # Slightly bullish - lime
                {'range': [30, 100], 'color': '#22c55e'},    # Bullish - green
            ],
            'threshold': {
                'line': {'color': "#1e293b", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=280,
        margin=dict(l=30, r=30, t=60, b=20),
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif"),
    )
    
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def options_volume_chart(options_data):
    """
    Create a chart showing Call vs Put volume comparison.
    """
    if not HAS_PLOTLY:
        return _placeholder()
    if not options_data or not options_data.get("available"):
        return "<p style='padding: 40px; text-align: center; color: #64748b;'>No options data available</p>"
    
    vol_data = options_data.get("volume", {})
    call_vol = int(vol_data.get("calls", 0) or 0)
    put_vol = int(vol_data.get("puts", 0) or 0)
    
    if call_vol == 0 and put_vol == 0:
        return "<p style='padding: 40px; text-align: center; color: #64748b;'>No volume data available for this expiration</p>"
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=["Calls", "Puts"],
        y=[call_vol, put_vol],
        marker_color=["#22c55e", "#ef4444"],
        text=[f"{call_vol:,}", f"{put_vol:,}"],
        textposition="outside",
    ))
    
    # Calculate appropriate y-axis range
    max_val = max(call_vol, put_vol)
    
    fig.update_layout(
        title="Options Volume (Calls vs Puts)",
        yaxis_title="Volume",
        yaxis=dict(range=[0, max_val * 1.2]),  # Add 20% padding
        showlegend=False,
        height=300,
        margin=dict(l=60, r=20, t=50, b=40),
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif", size=12),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
    )
    
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def options_oi_chart(options_data):
    """
    Create a chart showing Call vs Put open interest comparison.
    """
    if not HAS_PLOTLY:
        return _placeholder()
    if not options_data or not options_data.get("available"):
        return "<p style='padding: 40px; text-align: center; color: #64748b;'>No options data available</p>"
    
    oi_data = options_data.get("open_interest", {})
    call_oi = int(oi_data.get("calls", 0) or 0)
    put_oi = int(oi_data.get("puts", 0) or 0)
    
    if call_oi == 0 and put_oi == 0:
        return "<p style='padding: 40px; text-align: center; color: #64748b;'>No open interest data available for this expiration</p>"
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=["Calls", "Puts"],
        y=[call_oi, put_oi],
        marker_color=["#22c55e", "#ef4444"],
        text=[f"{call_oi:,}", f"{put_oi:,}"],
        textposition="outside",
    ))
    
    # Calculate appropriate y-axis range
    max_val = max(call_oi, put_oi)
    
    fig.update_layout(
        title="Open Interest (Calls vs Puts)",
        yaxis_title="Open Interest",
        yaxis=dict(range=[0, max_val * 1.2]),  # Add 20% padding
        showlegend=False,
        height=300,
        margin=dict(l=60, r=20, t=50, b=40),
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif", size=12),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
    )
    
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def sector_heatmap(sector_data):
    """
    Create a sector performance heatmap.
    """
    if not HAS_PLOTLY:
        return _placeholder()
    if not sector_data:
        return "<p style='padding: 40px; text-align: center; color: #64748b;'>No sector data available</p>"
    
    names = [s["name"] for s in sector_data]
    changes = [s["weekly_change"] for s in sector_data]
    
    # Color scale: red for negative, green for positive
    colors = ['#ef4444' if c < -1 else '#f97316' if c < 0 else '#84cc16' if c < 1 else '#22c55e' for c in changes]
    
    fig = go.Figure(data=[
        go.Bar(
            x=changes,
            y=names,
            orientation='h',
            marker_color=colors,
            text=[f"{c:+.1f}%" for c in changes],
            textposition='outside',
            textfont=dict(size=11),
        )
    ])
    
    fig.update_layout(
        title="Sector Performance (1 Week)",
        xaxis_title="Change (%)",
        yaxis={'categoryorder': 'total ascending'},
        height=380,
        margin=dict(l=120, r=60, t=50, b=40),
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif", size=12),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
    )
    
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def calculate_beta(ticker_history, benchmark_history):
    """
    Calculate beta of stock relative to benchmark.
    Beta = Covariance(stock, benchmark) / Variance(benchmark)
    """
    if not ticker_history or not benchmark_history or len(ticker_history) < 30:
        return None
    
    # Calculate daily returns
    stock_returns = []
    bench_returns = []
    
    # Align dates
    stock_dict = {p.date: p.close for p in ticker_history}
    bench_dict = {p.date: p.close for p in benchmark_history}
    
    common_dates = sorted(set(stock_dict.keys()) & set(bench_dict.keys()))
    
    if len(common_dates) < 30:
        return None
    
    prev_stock = None
    prev_bench = None
    for date in common_dates:
        if prev_stock is not None and prev_bench is not None:
            stock_ret = (stock_dict[date] / prev_stock) - 1
            bench_ret = (bench_dict[date] / prev_bench) - 1
            stock_returns.append(stock_ret)
            bench_returns.append(bench_ret)
        prev_stock = stock_dict[date]
        prev_bench = bench_dict[date]
    
    if len(stock_returns) < 20:
        return None
    
    # Calculate covariance and variance
    n = len(stock_returns)
    mean_stock = sum(stock_returns) / n
    mean_bench = sum(bench_returns) / n
    
    covariance = sum((s - mean_stock) * (b - mean_bench) for s, b in zip(stock_returns, bench_returns)) / n
    variance = sum((b - mean_bench) ** 2 for b in bench_returns) / n
    
    if variance == 0:
        return None
    
    return covariance / variance


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
