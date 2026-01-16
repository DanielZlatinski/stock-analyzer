def _signal_class(signal):
    """Return CSS class for signal coloring."""
    if signal == "Positive":
        return "signal-positive"
    if signal == "Negative":
        return "signal-negative"
    return "signal-neutral"


def _signal_label(value, positive_threshold=0.05, negative_threshold=-0.05):
    if value is None:
        return "Neutral"
    if value >= positive_threshold:
        return "Positive"
    if value <= negative_threshold:
        return "Negative"
    return "Neutral"


def _impact_word(signal):
    if signal == "Positive":
        return "strengthens"
    if signal == "Negative":
        return "weakens"
    return "has no clear effect on"


def build_chart_insights(ticker, snapshot, analysis, benchmark_prices):
    insights = {}

    # Price chart
    price_history = snapshot.price_history
    price_change = None
    if price_history:
        price_change = (price_history[-1].close / price_history[0].close) - 1
    signal = _signal_label(price_change)
    pct = f"{round(price_change * 100, 1)}%" if price_change is not None else "N/A"
    insights["price"] = {
        "summary": f"Price action with moving averages. Change: {pct}.",
        "signal": signal,
        "signal_class": _signal_class(signal),
        "impact": f"{signal} — {_impact_word(signal)} the investment case.",
    }

    # Relative performance
    relative_change = None
    if price_history and benchmark_prices:
        relative_change = (
            (price_history[-1].close / price_history[0].close)
            - (benchmark_prices[-1].close / benchmark_prices[0].close)
        )
    signal = _signal_label(relative_change)
    rel_pct = f"{round(relative_change * 100, 1)}%" if relative_change is not None else "N/A"
    insights["relative"] = {
        "summary": f"Performance vs benchmark. Relative: {rel_pct}.",
        "signal": signal,
        "signal_class": _signal_class(signal),
        "impact": f"{signal} — {_impact_word(signal)} the investment case.",
    }

    # Volume chart
    volume_signal = "Neutral"
    vol_note = "Average activity"
    if price_history:
        volumes = [p.volume for p in price_history if p.volume]
        if volumes:
            avg = sum(volumes) / len(volumes)
            last = volumes[-1]
            if last >= avg * 1.5:
                vol_note = "Elevated volume"
            elif last <= avg * 0.7:
                vol_note = "Low volume"
    insights["volume"] = {
        "summary": f"Daily trading volume. {vol_note}.",
        "signal": volume_signal,
        "signal_class": _signal_class(volume_signal),
        "impact": f"{volume_signal} — volume alone is not directional.",
    }

    # Rolling volatility
    vol_signal = "Neutral"
    vol_pct = "N/A"
    if analysis.price.annualized_volatility is not None:
        vol_value = analysis.price.annualized_volatility
        vol_pct = f"{round(vol_value * 100, 1)}%"
        if vol_value >= 0.4:
            vol_signal = "Negative"
        elif vol_value <= 0.2:
            vol_signal = "Positive"
    insights["volatility"] = {
        "summary": f"Rolling 20-day volatility. Current: {vol_pct}.",
        "signal": vol_signal,
        "signal_class": _signal_class(vol_signal),
        "impact": f"{vol_signal} — {_impact_word(vol_signal)} the investment case.",
    }

    # Fundamentals trend
    revenue_series = analysis.fundamentals.time_series.get("revenue", {})
    fundamental_signal = "Neutral"
    fund_note = "Mixed data"
    if revenue_series and len(revenue_series) >= 2:
        sorted_keys = sorted(revenue_series.keys())
        first = revenue_series[sorted_keys[0]]
        last = revenue_series[sorted_keys[-1]]
        if first:
            change = (last / first) - 1
            fund_note = f"Revenue change: {round(change * 100, 1)}%"
            fundamental_signal = _signal_label(change)
    insights["fundamentals"] = {
        "summary": f"Revenue, income, and cash flow trends. {fund_note}.",
        "signal": fundamental_signal,
        "signal_class": _signal_class(fundamental_signal),
        "impact": f"{fundamental_signal} — {_impact_word(fundamental_signal)} the investment case.",
    }

    # Peers chart
    peer_signal = "Neutral"
    peer_note = "No peer data"
    if analysis.peers.peer_metrics:
        peer_values = [m.get("pe_ratio") for m in analysis.peers.peer_metrics if m.get("pe_ratio")]
        ticker_pe = analysis.fundamentals.valuation.get("pe_ratio")
        if peer_values and ticker_pe:
            median = sorted(peer_values)[len(peer_values) // 2]
            if ticker_pe < median:
                peer_signal = "Positive"
                peer_note = "Below peer median P/E"
            elif ticker_pe > median:
                peer_signal = "Negative"
                peer_note = "Above peer median P/E"
            else:
                peer_note = "Near peer median P/E"
    insights["peers"] = {
        "summary": f"P/E vs peers. {peer_note}.",
        "signal": peer_signal,
        "signal_class": _signal_class(peer_signal),
        "impact": f"{peer_signal} — {_impact_word(peer_signal)} the investment case.",
    }

    # Sentiment chart
    sentiment_signal = "Neutral"
    news_count = len(snapshot.news) if snapshot.news else 0
    insights["sentiment"] = {
        "summary": f"Recent news volume. {news_count} items.",
        "signal": sentiment_signal,
        "signal_class": _signal_class(sentiment_signal),
        "impact": f"{sentiment_signal} — volume alone is not directional.",
    }

    # Recommendation waterfall
    rec_signal = "Neutral"
    score = analysis.recommendation.score
    if score >= 70:
        rec_signal = "Positive"
    elif score < 45:
        rec_signal = "Negative"
    top_driver = None
    if analysis.recommendation.contributions:
        top_driver = max(analysis.recommendation.contributions, key=analysis.recommendation.contributions.get)
    driver_text = top_driver.title() if top_driver else "Mixed"
    insights["recommendation"] = {
        "summary": f"Score breakdown by factor. Top driver: {driver_text}.",
        "signal": rec_signal,
        "signal_class": _signal_class(rec_signal),
        "impact": f"{rec_signal} — total score: {round(score, 1)}.",
    }

    return insights
