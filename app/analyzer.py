def score_snapshot(snapshot):
    reasons = []
    score = 0

    pe_ratio = snapshot.get("pe_ratio")
    if pe_ratio is not None:
        if pe_ratio < 25:
            score += 1
            reasons.append("P/E is under 25 (reasonable valuation).")
        else:
            reasons.append("P/E is above 25 (richer valuation).")

    roe = snapshot.get("roe")
    if roe is not None:
        if roe > 0.10:
            score += 1
            reasons.append("ROE is above 10% (strong profitability).")
        else:
            reasons.append("ROE is below 10% (weaker profitability).")

    debt_to_equity = snapshot.get("debt_to_equity")
    if debt_to_equity is not None:
        if debt_to_equity < 1:
            score += 1
            reasons.append("Debt-to-equity is below 1 (healthy leverage).")
        else:
            reasons.append("Debt-to-equity is above 1 (higher leverage).")

    revenue_growth = snapshot.get("revenue_growth")
    if revenue_growth is not None:
        if revenue_growth > 0.05:
            score += 1
            reasons.append("Revenue growth is above 5%.")
        else:
            reasons.append("Revenue growth is below 5%.")

    decision = "INVEST" if score >= 3 else "DON'T INVEST"
    return {
        "decision": decision,
        "score": score,
        "reasons": reasons,
    }
