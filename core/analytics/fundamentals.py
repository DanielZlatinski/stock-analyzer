from core.analysis_models import FundamentalAnalytics


def _extract_series(statement, field):
    series = {}
    if not statement:
        return series
    for period, values in statement.items():
        if field in values:
            series[period] = float(values[field])
    return series


def _latest_from_series(series):
    if not series:
        return None
    sorted_keys = sorted(series.keys(), reverse=True)
    return series[sorted_keys[0]]


def _growth_from_series(series):
    if len(series) < 2:
        return None
    sorted_keys = sorted(series.keys(), reverse=True)
    latest = series[sorted_keys[0]]
    prev = series[sorted_keys[1]]
    if prev == 0:
        return None
    return (latest / prev) - 1


def _assess_valuation(fundamentals):
    """Generate a valuation assessment based on multiple metrics."""
    assessments = []
    score = 0
    count = 0
    
    pe = fundamentals.get("pe_ratio")
    fwd_pe = fundamentals.get("forward_pe")
    peg = fundamentals.get("peg_ratio")
    pb = fundamentals.get("price_to_book")
    ps = fundamentals.get("price_to_sales")
    ev_ebitda = fundamentals.get("ev_to_ebitda")
    
    # P/E assessment
    if pe:
        count += 1
        if pe < 15:
            score += 2
            assessments.append(("P/E", "attractive", f"P/E of {pe:.1f} is below 15, suggesting potential undervaluation"))
        elif pe < 25:
            score += 1
            assessments.append(("P/E", "fair", f"P/E of {pe:.1f} is in a reasonable range"))
        else:
            assessments.append(("P/E", "elevated", f"P/E of {pe:.1f} is elevated, pricing in high growth expectations"))
    
    # Forward P/E vs Trailing P/E
    if pe and fwd_pe:
        if fwd_pe < pe * 0.85:
            assessments.append(("Earnings Growth", "positive", f"Forward P/E ({fwd_pe:.1f}) significantly below trailing ({pe:.1f}), indicating expected earnings growth"))
        elif fwd_pe > pe * 1.1:
            assessments.append(("Earnings Outlook", "caution", f"Forward P/E ({fwd_pe:.1f}) above trailing ({pe:.1f}), suggesting earnings pressure ahead"))
    
    # PEG ratio
    if peg:
        count += 1
        if peg < 1:
            score += 2
            assessments.append(("PEG", "attractive", f"PEG of {peg:.2f} below 1 suggests undervaluation relative to growth"))
        elif peg < 2:
            score += 1
            assessments.append(("PEG", "fair", f"PEG of {peg:.2f} indicates reasonable valuation for growth rate"))
        else:
            assessments.append(("PEG", "elevated", f"PEG of {peg:.2f} suggests premium valuation vs growth"))
    
    # Price/Book
    if pb:
        count += 1
        if pb < 3:
            score += 1
            assessments.append(("P/B", "reasonable", f"Price/Book of {pb:.2f} is reasonable"))
        elif pb > 10:
            assessments.append(("P/B", "elevated", f"Price/Book of {pb:.2f} is elevated"))
    
    # EV/EBITDA
    if ev_ebitda:
        count += 1
        if ev_ebitda < 10:
            score += 2
            assessments.append(("EV/EBITDA", "attractive", f"EV/EBITDA of {ev_ebitda:.1f} below 10 is attractive"))
        elif ev_ebitda < 15:
            score += 1
            assessments.append(("EV/EBITDA", "fair", f"EV/EBITDA of {ev_ebitda:.1f} is in fair range"))
        else:
            assessments.append(("EV/EBITDA", "elevated", f"EV/EBITDA of {ev_ebitda:.1f} is premium"))
    
    # Overall verdict
    if count > 0:
        avg_score = score / count
        if avg_score >= 1.5:
            verdict = "Undervalued"
            verdict_detail = "Multiple valuation metrics suggest the stock may be undervalued relative to fundamentals."
        elif avg_score >= 0.75:
            verdict = "Fairly Valued"
            verdict_detail = "Valuation metrics suggest the stock is trading near fair value."
        else:
            verdict = "Premium Valuation"
            verdict_detail = "The stock trades at a premium, reflecting high growth expectations or market optimism."
    else:
        verdict = "Insufficient Data"
        verdict_detail = "Not enough valuation data to make an assessment."
    
    return {
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "assessments": assessments,
        "score": score,
        "max_score": count * 2 if count > 0 else 1,
    }


def build_fundamental_analytics(fundamentals, financials):
    income_statement = financials.get("income_statement", {})
    cash_flow = financials.get("cash_flow", {})
    balance_sheet_data = financials.get("balance_sheet", {})

    revenue_series = _extract_series(income_statement, "Total Revenue")
    net_income_series = _extract_series(income_statement, "Net Income")
    ebitda_series = _extract_series(income_statement, "EBITDA")
    fcf_series = _extract_series(cash_flow, "Free Cash Flow")

    # Calculate price vs 52-week range
    current_price = fundamentals.get("current_price")
    high_52w = fundamentals.get("fifty_two_week_high")
    low_52w = fundamentals.get("fifty_two_week_low")
    pct_from_high = None
    pct_from_low = None
    range_position = None
    if current_price and high_52w and low_52w and high_52w != low_52w:
        pct_from_high = (current_price - high_52w) / high_52w
        pct_from_low = (current_price - low_52w) / low_52w
        range_position = (current_price - low_52w) / (high_52w - low_52w)  # 0 = at low, 1 = at high

    # Calculate upside to analyst target
    target_price = fundamentals.get("target_mean_price")
    upside_to_target = None
    if current_price and target_price:
        upside_to_target = (target_price - current_price) / current_price

    valuation = {
        "pe_ratio": fundamentals.get("pe_ratio"),
        "forward_pe": fundamentals.get("forward_pe"),
        "peg_ratio": fundamentals.get("peg_ratio"),
        "price_to_book": fundamentals.get("price_to_book"),
        "price_to_sales": fundamentals.get("price_to_sales"),
        "ev_to_ebitda": fundamentals.get("ev_to_ebitda"),
        "ev_to_revenue": fundamentals.get("ev_to_revenue"),
        "market_cap": fundamentals.get("market_cap"),
        "enterprise_value": fundamentals.get("enterprise_value"),
        "book_value": fundamentals.get("book_value"),
        "current_price": current_price,
        "fifty_two_week_high": high_52w,
        "fifty_two_week_low": low_52w,
        "pct_from_52w_high": pct_from_high,
        "pct_from_52w_low": pct_from_low,
        "range_position_52w": range_position,
        "fifty_day_average": fundamentals.get("fifty_day_average"),
        "two_hundred_day_average": fundamentals.get("two_hundred_day_average"),
        "target_mean_price": target_price,
        "target_high_price": fundamentals.get("target_high_price"),
        "target_low_price": fundamentals.get("target_low_price"),
        "upside_to_target": upside_to_target,
        "number_of_analysts": fundamentals.get("number_of_analysts"),
        "recommendation_key": fundamentals.get("recommendation_key"),
        "assessment": _assess_valuation(fundamentals),
    }
    
    dividend = {
        "dividend_yield": fundamentals.get("dividend_yield"),
        "dividend_rate": fundamentals.get("dividend_rate"),
        "payout_ratio": fundamentals.get("payout_ratio"),
        "five_year_avg_dividend_yield": fundamentals.get("five_year_avg_dividend_yield"),
    }
    
    profitability = {
        "roe": fundamentals.get("roe"),
        "roa": fundamentals.get("roa"),
        "gross_margins": fundamentals.get("gross_margins"),
        "operating_margins": fundamentals.get("operating_margins"),
        "profit_margins": fundamentals.get("profit_margins"),
    }
    growth = {
        "revenue_growth": fundamentals.get("revenue_growth"),
        "earnings_growth": fundamentals.get("earnings_growth"),
        "earnings_quarterly_growth": fundamentals.get("earnings_quarterly_growth"),
        "revenue_growth_1y": _growth_from_series(revenue_series),
        "net_income_growth_1y": _growth_from_series(net_income_series),
        "fcf_growth_1y": _growth_from_series(fcf_series),
    }
    balance_sheet_metrics = {
        "debt_to_equity": fundamentals.get("debt_to_equity"),
        "current_ratio": fundamentals.get("current_ratio"),
        "quick_ratio": fundamentals.get("quick_ratio"),
        "total_cash": fundamentals.get("total_cash"),
        "total_debt": fundamentals.get("total_debt"),
        "free_cash_flow": fundamentals.get("free_cash_flow"),
    }
    
    per_share = {
        "eps_trailing": fundamentals.get("eps_trailing"),
        "eps_forward": fundamentals.get("eps_forward"),
        "revenue_per_share": fundamentals.get("revenue_per_share"),
        "book_value": fundamentals.get("book_value"),
    }

    time_series = {
        "revenue": revenue_series,
        "net_income": net_income_series,
        "ebitda": ebitda_series,
        "free_cash_flow": fcf_series,
    }

    return FundamentalAnalytics(
        valuation=valuation,
        profitability=profitability,
        growth=growth,
        balance_sheet=balance_sheet_metrics,
        time_series=time_series,
        dividend=dividend,
        per_share=per_share,
    )
