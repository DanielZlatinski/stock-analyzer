"""
Comprehensive Scoring Service for Investment Recommendations

This module calculates a final investment score based on multiple factors:
- Technical Analysis (18%): Price trends, momentum indicators, RSI, MACD
- Fundamentals (22%): Quality metrics (ROE, margins) + Growth metrics
- Valuation (20%): P/E, Forward P/E, PEG, EV/EBITDA relative attractiveness
- Momentum (12%): Recent price performance
- Risk (12%): Volatility, beta, max drawdown - lower is better
- Market (8%): Market sentiment and sector performance
- Sentiment (8%): News sentiment analysis

Final Score Interpretation:
- 58-100: INVEST - Strong buy signal with favorable metrics
- 42-57: WATCH - Hold/Monitor, mixed signals or fair value
- 0-41: AVOID - Unfavorable risk/reward or deteriorating fundamentals

Special Handling:
- ETFs: Only scored on Technical, Risk, Momentum, Market factors (no fundamentals/valuation)
"""

from core.analysis_models import Recommendation
from core.scoring_config import SCORE_WEIGHTS, THRESHOLDS, ETF_SCORE_WEIGHTS, TIMING_THRESHOLDS


def _scale(value, min_val, max_val, invert=False):
    """Scale a value to 0-100 range."""
    if value is None:
        return None
    if min_val == max_val:
        return 50
    score = (value - min_val) / (max_val - min_val) * 100
    score = max(0, min(100, score))
    return 100 - score if invert else score


def _avg(values):
    """Calculate average of non-None values."""
    filtered = [v for v in values if v is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def _signal_from_score(score):
    """Convert score to signal label."""
    if score is None:
        return "neutral"
    if score >= 65:
        return "positive"
    if score <= 35:
        return "negative"
    return "neutral"


class ScoringService:
    def score(self, analysis, completeness_percent, quote_type=None, sector=None):
        """
        Calculate comprehensive investment score with detailed breakdowns.
        
        Args:
            analysis: AnalysisPack with all analysis data
            completeness_percent: Data quality percentage
            quote_type: 'EQUITY', 'ETF', 'MUTUALFUND', etc.
            sector: Company sector for market scoring (e.g., 'Technology')
        """
        is_etf = quote_type == "ETF"
        weights = ETF_SCORE_WEIGHTS if is_etf else SCORE_WEIGHTS
        # ============================================================
        # TECHNICAL SCORE (20% weight)
        # Based on: trend direction, RSI positioning, MACD signals
        # ============================================================
        trend_1m = analysis.technicals.trend_by_horizon.get("1m", "").lower()
        trend_3m = analysis.technicals.trend_by_horizon.get("3m", "").lower()
        trend_1w = analysis.technicals.trend_by_horizon.get("1w", "").lower()
        
        # Trend scoring: bullish = 75, bearish = 25, neutral = 50
        trend_scores = []
        if trend_1w:
            trend_scores.append(75 if trend_1w == "bullish" else 25 if trend_1w == "bearish" else 50)
        if trend_1m:
            trend_scores.append(75 if trend_1m == "bullish" else 25 if trend_1m == "bearish" else 50)
        if trend_3m:
            trend_scores.append(75 if trend_3m == "bullish" else 25 if trend_3m == "bearish" else 50)
        
        trend_score = _avg(trend_scores) if trend_scores else 50
        
        # RSI: 30-70 is ideal, extremes are less favorable
        rsi = analysis.technicals.rsi_14
        if rsi is not None:
            if 40 <= rsi <= 60:
                rsi_score = 70  # Neutral zone - good
            elif 30 <= rsi < 40 or 60 < rsi <= 70:
                rsi_score = 55  # Slightly extended
            elif rsi < 30:
                rsi_score = 65  # Oversold - potential bounce (bullish)
            else:
                rsi_score = 35  # Overbought - potential pullback (bearish)
        else:
            rsi_score = None
        
        # MACD: positive histogram is bullish
        macd = analysis.technicals.macd
        macd_signal = analysis.technicals.macd_signal
        if macd is not None and macd_signal is not None:
            macd_score = 70 if macd > macd_signal else 30
        else:
            macd_score = None
        
        technical_score = _avg([trend_score, rsi_score, macd_score])
        
        technical_details = {
            "score": technical_score,
            "signal": _signal_from_score(technical_score),
            "trend": f"{trend_1m.title() if trend_1m else 'N/A'} (1M)",
            "rsi": f"{rsi:.1f}" if rsi else "N/A",
            "rsi_signal": "Oversold" if rsi and rsi < 30 else "Overbought" if rsi and rsi > 70 else "Normal" if rsi else "N/A",
            "macd_signal": "Bullish" if macd and macd_signal and macd > macd_signal else "Bearish" if macd and macd_signal else "N/A",
            "explanation": self._explain_technical(trend_1m, rsi, macd, macd_signal),
        }
        
        # ============================================================
        # FUNDAMENTAL SCORE (25% weight)
        # Quality (ROE, margins) + Growth (revenue, earnings)
        # ============================================================
        # Quality metrics
        roe = analysis.fundamentals.profitability.get("roe")
        roa = analysis.fundamentals.profitability.get("roa")
        operating_margin = analysis.fundamentals.profitability.get("operating_margins")
        profit_margin = analysis.fundamentals.profitability.get("profit_margins")
        
        quality_score = _avg([
            _scale(roe, 0, 0.30),  # ROE: 0-30% range
            _scale(operating_margin, 0, 0.30),  # Op margin: 0-30%
            _scale(profit_margin, 0, 0.25),  # Net margin: 0-25%
        ])
        
        # Growth metrics
        revenue_growth = analysis.fundamentals.growth.get("revenue_growth")
        earnings_growth = analysis.fundamentals.growth.get("earnings_growth")
        
        growth_score = _avg([
            _scale(revenue_growth, -0.20, 0.40),  # -20% to +40%
            _scale(earnings_growth, -0.30, 0.50),  # -30% to +50%
        ])
        
        fundamental_score = _avg([quality_score, growth_score])
        
        fundamental_details = {
            "score": fundamental_score,
            "signal": _signal_from_score(fundamental_score),
            "quality_score": quality_score,
            "growth_score": growth_score,
            "roe": f"{roe*100:.1f}%" if roe else "N/A",
            "revenue_growth": f"{revenue_growth*100:.1f}%" if revenue_growth else "N/A",
            "explanation": self._explain_fundamental(roe, revenue_growth, earnings_growth),
        }
        
        # ============================================================
        # VALUATION SCORE (20% weight)
        # Lower multiples = higher score (inverted)
        # ============================================================
        pe = analysis.fundamentals.valuation.get("pe_ratio")
        forward_pe = analysis.fundamentals.valuation.get("forward_pe")
        peg = analysis.fundamentals.valuation.get("peg_ratio")
        pb = analysis.fundamentals.valuation.get("price_to_book")
        ev_ebitda = analysis.fundamentals.valuation.get("ev_to_ebitda")
        
        valuation_subscores = [
            _scale(pe, 5, 40, invert=True) if pe else None,
            _scale(forward_pe, 5, 35, invert=True) if forward_pe else None,
            _scale(peg, 0.5, 3, invert=True) if peg else None,
            _scale(ev_ebitda, 5, 25, invert=True) if ev_ebitda else None,
        ]
        
        valuation_score = _avg(valuation_subscores)
        
        valuation_details = {
            "score": valuation_score,
            "signal": _signal_from_score(valuation_score),
            "pe": f"{pe:.1f}" if pe else "N/A",
            "forward_pe": f"{forward_pe:.1f}" if forward_pe else "N/A",
            "peg": f"{peg:.2f}" if peg else "N/A",
            "explanation": self._explain_valuation(pe, forward_pe, peg),
        }
        
        # ============================================================
        # RISK SCORE (15% weight)
        # Lower risk = higher score (inverted for most metrics)
        # ============================================================
        volatility = analysis.risk.get("volatility")
        beta = analysis.risk.get("beta")
        max_drawdown = analysis.risk.get("max_drawdown")
        
        risk_subscores = [
            _scale(volatility, 0.15, 0.50, invert=True) if volatility else None,
            _scale(beta, 0.5, 2.0, invert=True) if beta else None,
            _scale(max_drawdown, -0.50, -0.05, invert=False) if max_drawdown else None,  # Less negative = better
        ]
        
        risk_score = _avg(risk_subscores)
        
        risk_details = {
            "score": risk_score,
            "signal": _signal_from_score(risk_score),
            "volatility": f"{volatility*100:.1f}%" if volatility else "N/A",
            "beta": f"{beta:.2f}" if beta else "N/A",
            "max_drawdown": f"{max_drawdown*100:.1f}%" if max_drawdown else "N/A",
            "explanation": self._explain_risk(volatility, beta, max_drawdown),
        }
        
        # ============================================================
        # SENTIMENT SCORE (10% weight)
        # News sentiment analysis
        # ============================================================
        headline_score = analysis.sentiment.headline_score
        positive_pct = analysis.sentiment.positive_count / max(analysis.sentiment.headline_volume, 1) if analysis.sentiment.headline_volume > 0 else 0
        negative_pct = analysis.sentiment.negative_count / max(analysis.sentiment.headline_volume, 1) if analysis.sentiment.headline_volume > 0 else 0
        
        sentiment_subscores = [
            _scale(headline_score, -0.5, 0.5) if headline_score is not None else None,
            _scale(positive_pct - negative_pct, -0.5, 0.5) if analysis.sentiment.headline_volume > 0 else None,
        ]
        
        sentiment_score = _avg(sentiment_subscores) if any(s is not None for s in sentiment_subscores) else 50
        
        sentiment_details = {
            "score": sentiment_score,
            "signal": _signal_from_score(sentiment_score),
            "headline_score": f"{headline_score:.2f}" if headline_score else "N/A",
            "positive_count": analysis.sentiment.positive_count,
            "negative_count": analysis.sentiment.negative_count,
            "overall": analysis.sentiment.overall_sentiment,
            "explanation": self._explain_sentiment(headline_score, analysis.sentiment.positive_count, analysis.sentiment.negative_count),
        }
        
        # ============================================================
        # MOMENTUM SCORE (10% weight)
        # Recent price performance
        # ============================================================
        total_return = analysis.price.total_return
        rolling_3m = analysis.price.rolling_returns.get("3m")
        rolling_1m = analysis.price.rolling_returns.get("1m")
        
        momentum_subscores = [
            _scale(total_return, -0.30, 0.50) if total_return else None,
            _scale(rolling_3m, -0.20, 0.30) if rolling_3m else None,
            _scale(rolling_1m, -0.10, 0.15) if rolling_1m else None,
        ]
        
        momentum_score = _avg(momentum_subscores)
        
        momentum_details = {
            "score": momentum_score,
            "signal": _signal_from_score(momentum_score),
            "total_return": f"{total_return*100:.1f}%" if total_return else "N/A",
            "rolling_3m": f"{rolling_3m*100:.1f}%" if rolling_3m else "N/A",
            "explanation": self._explain_momentum(total_return, rolling_3m),
        }
        
        # ============================================================
        # MARKET & SECTOR SCORE (8% weight)
        # Overall market conditions and sector performance
        # ============================================================
        market_score = 50  # Default neutral
        market_explanation = "Market data not available."
        sector_name = sector  # Use passed sector parameter
        
        # Sector to ETF mapping
        sector_etf_map = {
            "Technology": "XLK",
            "Financial Services": "XLF",
            "Healthcare": "XLV",
            "Energy": "XLE",
            "Industrials": "XLI",
            "Consumer Cyclical": "XLY",
            "Consumer Defensive": "XLP",
            "Utilities": "XLU",
            "Basic Materials": "XLB",
            "Real Estate": "XLRE",
            "Communication Services": "XLC",
        }
        
        try:
            from core.analytics.market_sentiment import analyze_market_sentiment, get_sector_performance
            
            # Get market sentiment
            market_data = analyze_market_sentiment()
            market_sentiment_score = market_data.get("score", 0)
            
            # Scale market sentiment from -100/+100 to 0-100
            market_component = (market_sentiment_score + 100) / 2
            
            # Get sector performance
            sectors = get_sector_performance()
            sector_component = 50  # Default
            
            # Match company's sector to sector ETF performance
            if sector_name and sector_name in sector_etf_map:
                target_etf = sector_etf_map[sector_name]
                for sector_data in sectors:
                    if sector_data.get("ticker") == target_etf:
                        sector_change = sector_data.get("weekly_change", 0)
                        # Scale sector change: -5% to +5% -> 0 to 100
                        sector_component = _scale(sector_change, -5, 5) or 50
                        break
            else:
                # If no sector match, use average of all sectors
                all_changes = [s.get("weekly_change", 0) for s in sectors if s.get("weekly_change") is not None]
                if all_changes:
                    avg_change = sum(all_changes) / len(all_changes)
                    sector_component = _scale(avg_change, -5, 5) or 50
            
            # Combine market sentiment (60%) and sector (40%)
            market_score = (market_component * 0.6) + (sector_component * 0.4)
            
            sentiment_label = market_data.get("sentiment", "Neutral")
            market_explanation = f"Market is {sentiment_label}. "
            if sector_name:
                market_explanation += f"Sector ({sector_name}) showing recent momentum."
            
        except Exception as e:
            market_explanation = "Unable to analyze market conditions."
        
        market_details = {
            "score": market_score,
            "signal": _signal_from_score(market_score),
            "sector": sector_name or "N/A",
            "explanation": market_explanation,
        }
        
        # ============================================================
        # PEERS SCORE (7% weight)
        # How does this stock compare to its peers?
        # ============================================================
        peers_score = 50  # Default neutral
        peers_explanation = "Limited peer data available."
        
        peer_ranks = analysis.peers.percentile_ranks if analysis.peers else {}
        if peer_ranks:
            peer_subscores = []
            
            # P/E rank: lower is better (cheaper valuation)
            pe_rank = peer_ranks.get("pe_ratio")
            if pe_rank is not None:
                # Invert: low percentile (cheap) = high score
                peer_subscores.append(100 - pe_rank)
            
            # Forward P/E rank: lower is better
            fwd_pe_rank = peer_ranks.get("forward_pe")
            if fwd_pe_rank is not None:
                peer_subscores.append(100 - fwd_pe_rank)
            
            # ROE rank: higher is better (more profitable)
            roe_rank = peer_ranks.get("roe")
            if roe_rank is not None:
                peer_subscores.append(roe_rank)
            
            # Revenue growth rank: higher is better
            rev_rank = peer_ranks.get("revenue_growth")
            if rev_rank is not None:
                peer_subscores.append(rev_rank)
            
            # Debt/Equity rank: lower is better (less leveraged)
            de_rank = peer_ranks.get("debt_to_equity")
            if de_rank is not None:
                peer_subscores.append(100 - de_rank)
            
            if peer_subscores:
                peers_score = _avg(peer_subscores)
                
                # Build explanation
                strengths = []
                weaknesses = []
                if pe_rank is not None:
                    if pe_rank < 30:
                        strengths.append("cheaper valuation than most peers")
                    elif pe_rank > 70:
                        weaknesses.append("more expensive than peers")
                if roe_rank is not None:
                    if roe_rank > 70:
                        strengths.append("higher profitability")
                    elif roe_rank < 30:
                        weaknesses.append("lower profitability")
                
                if strengths:
                    peers_explanation = f"Ranks favorably: {', '.join(strengths)}."
                elif weaknesses:
                    peers_explanation = f"Ranks below peers: {', '.join(weaknesses)}."
                else:
                    peers_explanation = "Ranks near peer average on key metrics."
        
        peers_details = {
            "score": peers_score,
            "signal": _signal_from_score(peers_score),
            "pe_rank": peer_ranks.get("pe_ratio"),
            "roe_rank": peer_ranks.get("roe"),
            "explanation": peers_explanation,
        }
        
        # ============================================================
        # CALCULATE FINAL WEIGHTED SCORE
        # ============================================================
        scores = {
            "technical": technical_score or 50,
            "momentum": momentum_score or 50,
            "fundamental": fundamental_score or 50 if not is_etf else 50,
            "valuation": valuation_score or 50 if not is_etf else 50,
            "peers": peers_score or 50 if not is_etf else 50,
            "market": market_score or 50,
            "sentiment": sentiment_score or 50,
            "risk": risk_score or 50,
        }
        
        weighted_total = 0
        for key, weight in weights.items():  # Use dynamic weights (ETF vs equity)
            weighted_total += scores[key] * weight
        
        weighted_total = max(0, min(100, weighted_total))
        
        # ============================================================
        # CALCULATE TIMING SIGNAL (Entry Point Quality)
        # ============================================================
        timing_score = self._calculate_timing_signal(analysis)
        if timing_score >= TIMING_THRESHOLDS["excellent"]:
            timing_signal = "Excellent"
            timing_description = "Strong entry point. Technical indicators suggest favorable timing for new positions."
        elif timing_score >= TIMING_THRESHOLDS["good"]:
            timing_signal = "Good"
            timing_description = "Reasonable entry point. Some technical support for initiating positions."
        elif timing_score >= TIMING_THRESHOLDS["fair"]:
            timing_signal = "Fair"
            timing_description = "Neutral timing. Consider scaling in gradually or waiting for pullback."
        else:
            timing_signal = "Poor"
            timing_description = "Unfavorable entry. Price may be extended. Consider waiting for better levels."
        
        # ============================================================
        # DETERMINE RATING
        # ============================================================
        if weighted_total >= THRESHOLDS["invest"]:
            rating = "INVEST"
            if timing_signal in ["Excellent", "Good"]:
                rating_description = "Strong buy signal with favorable entry timing. Consider initiating or adding to positions."
            else:
                rating_description = "Fundamentally attractive but timing is suboptimal. Consider scaling in on pullbacks."
        elif weighted_total >= THRESHOLDS["watch"]:
            rating = "WATCH"
            rating_description = "Hold or monitor. Mixed signals or fair valuation. Wait for better entry point or improving fundamentals."
        else:
            rating = "AVOID"
            rating_description = "Unfavorable risk/reward. Deteriorating fundamentals, poor valuation, or excessive risk. Consider alternatives."
        
        # ============================================================
        # BUILD DETAILED OUTPUT
        # ============================================================
        confidence = self._calculate_confidence(weighted_total, completeness_percent, scores)
        positives, risks = self._build_reasoning(scores, technical_details, fundamental_details, valuation_details, risk_details, sentiment_details, momentum_details, market_details)
        triggers = self._build_triggers(scores, valuation_details, technical_details, sentiment_details)
        
        # Contributions for waterfall chart (use dynamic weights)
        contributions = {key: scores[key] * weights[key] for key in scores}
        
        # Factor details for Overview display
        factor_details = {
            "technical": technical_details,
            "momentum": momentum_details,
            "fundamental": fundamental_details,
            "valuation": valuation_details,
            "peers": peers_details,
            "market": market_details,
            "sentiment": sentiment_details,
            "risk": risk_details,
        }
        
        # For ETFs, update inapplicable factor explanations
        if is_etf:
            factor_details["fundamental"]["explanation"] = "Not applicable for ETFs."
            factor_details["valuation"]["explanation"] = "Not applicable for ETFs."
            factor_details["peers"]["explanation"] = "Not applicable for ETFs."
        
        return Recommendation(
            rating=rating,
            score=round(weighted_total, 1),
            confidence=confidence,
            contributions=contributions,
            positives=positives,
            risks=risks,
            triggers=triggers,
            rating_description=rating_description,
            factor_details=factor_details,
            factor_scores=scores,
            timing_signal=timing_signal,
            timing_score=round(timing_score, 1),
            timing_description=timing_description,
            is_etf=is_etf,
        )
    
    def _explain_technical(self, trend, rsi, macd, macd_signal):
        parts = []
        if trend:
            parts.append(f"Trend is {trend}")
        if rsi:
            if rsi < 30:
                parts.append("RSI oversold (potential bounce)")
            elif rsi > 70:
                parts.append("RSI overbought (potential pullback)")
            else:
                parts.append("RSI in neutral zone")
        if macd is not None and macd_signal is not None:
            parts.append("MACD bullish" if macd > macd_signal else "MACD bearish")
        return ". ".join(parts) + "." if parts else "Insufficient technical data."
    
    def _explain_fundamental(self, roe, rev_growth, earn_growth):
        parts = []
        if roe:
            if roe > 0.20:
                parts.append("Excellent ROE (>20%)")
            elif roe > 0.12:
                parts.append("Good ROE (>12%)")
            else:
                parts.append("Weak ROE (<12%)")
        if rev_growth:
            if rev_growth > 0.15:
                parts.append("Strong revenue growth")
            elif rev_growth > 0:
                parts.append("Positive revenue growth")
            else:
                parts.append("Revenue declining")
        return ". ".join(parts) + "." if parts else "Limited fundamental data."
    
    def _explain_valuation(self, pe, fwd_pe, peg):
        parts = []
        if pe:
            if pe < 15:
                parts.append("Low P/E suggests value")
            elif pe > 30:
                parts.append("High P/E reflects growth premium")
            else:
                parts.append("P/E in reasonable range")
        if peg:
            if peg < 1:
                parts.append("PEG < 1 (undervalued vs growth)")
            elif peg > 2:
                parts.append("PEG > 2 (expensive vs growth)")
        return ". ".join(parts) + "." if parts else "Limited valuation data."
    
    def _explain_risk(self, vol, beta, dd):
        parts = []
        if vol:
            if vol > 0.40:
                parts.append("High volatility (>40%)")
            elif vol < 0.20:
                parts.append("Low volatility (<20%)")
        if beta:
            if beta > 1.3:
                parts.append("High beta amplifies market moves")
            elif beta < 0.7:
                parts.append("Low beta provides stability")
        if dd:
            if dd < -0.30:
                parts.append("Large historical drawdown")
        return ". ".join(parts) + "." if parts else "Standard risk profile."
    
    def _explain_sentiment(self, score, pos, neg):
        if pos > neg * 2:
            return "News sentiment predominantly positive."
        elif neg > pos * 2:
            return "News sentiment predominantly negative."
        elif pos > 0 or neg > 0:
            return "Mixed news sentiment."
        return "Limited news coverage."
    
    def _explain_momentum(self, total, rolling_3m):
        if total and total > 0.20:
            return "Strong positive momentum."
        elif total and total > 0:
            return "Positive but modest momentum."
        elif total and total < -0.10:
            return "Negative momentum, price weakness."
        return "Neutral momentum."
    
    def _calculate_confidence(self, total_score, completeness, scores):
        # Check agreement between factors
        score_values = [v for v in scores.values() if v is not None]
        if len(score_values) < 3:
            return "Low"
        
        # Standard deviation of scores - lower = more agreement
        avg_score = sum(score_values) / len(score_values)
        variance = sum((s - avg_score) ** 2 for s in score_values) / len(score_values)
        std_dev = variance ** 0.5
        
        agreement_score = max(0, 100 - std_dev * 2)  # Lower std dev = higher agreement
        
        # Blend completeness and agreement
        blended = (completeness * 0.5) + (agreement_score * 0.5)
        
        if blended >= 75 and total_score >= 60:
            return "High"
        if blended >= 50:
            return "Medium"
        return "Low"
    
    def _build_reasoning(self, scores, tech, fund, val, risk, sent, mom, market=None):
        positives = []
        risks = []
        
        # Technical
        if scores["technical"] >= 60:
            positives.append(f"Technical outlook positive: {tech['explanation']}")
        elif scores["technical"] <= 40:
            risks.append(f"Technical weakness: {tech['explanation']}")
        
        # Fundamental
        if scores["fundamental"] >= 60:
            positives.append(f"Strong fundamentals: {fund['explanation']}")
        elif scores["fundamental"] <= 40:
            risks.append(f"Fundamental concerns: {fund['explanation']}")
        
        # Valuation
        if scores["valuation"] >= 60:
            positives.append(f"Attractive valuation: {val['explanation']}")
        elif scores["valuation"] <= 40:
            risks.append(f"Expensive valuation: {val['explanation']}")
        
        # Risk
        if scores["risk"] >= 60:
            positives.append(f"Favorable risk profile: {risk['explanation']}")
        elif scores["risk"] <= 40:
            risks.append(f"Elevated risk: {risk['explanation']}")
        
        # Sentiment
        if scores["sentiment"] >= 60:
            positives.append(f"Positive sentiment: {sent['explanation']}")
        elif scores["sentiment"] <= 40:
            risks.append(f"Negative sentiment: {sent['explanation']}")
        
        # Momentum
        if scores["momentum"] >= 60:
            positives.append(f"Strong momentum: {mom['explanation']}")
        elif scores["momentum"] <= 40:
            risks.append(f"Weak momentum: {mom['explanation']}")
        
        # Market conditions
        if scores.get("market", 50) >= 60:
            positives.append("Favorable market/sector conditions supporting the stock")
        elif scores.get("market", 50) <= 40:
            risks.append("Challenging market/sector headwinds")
        
        return positives[:5], risks[:5]
    
    def _build_triggers(self, scores, val, tech, sent):
        triggers = []
        
        if scores["valuation"] < 50:
            triggers.append("Valuation becomes more attractive (P/E contracts or earnings grow faster than price)")
        if scores["technical"] < 50:
            triggers.append("Technical trend turns bullish with price breaking above key moving averages")
        if scores["sentiment"] < 50:
            triggers.append("News sentiment shifts positive with sustained bullish coverage")
        if scores["risk"] < 50:
            triggers.append("Volatility decreases and risk metrics normalize")
        if scores["fundamental"] < 50:
            triggers.append("Earnings or revenue growth accelerates, margins expand")
        if scores["momentum"] < 50:
            triggers.append("Price momentum turns positive with higher highs and higher lows")
        if scores.get("market", 50) < 50:
            triggers.append("Market/sector conditions improve with broader rally")
        
        return triggers[:4]
    
    def _calculate_timing_signal(self, analysis):
        """
        Calculate timing score for entry point quality.
        
        Considers:
        - RSI position (oversold = better entry)
        - MACD crossover direction
        - Price relative to moving averages
        - Recent momentum
        - Volatility regime
        
        Returns score 0-100 where higher = better entry point.
        """
        timing_components = []
        
        # RSI positioning (0-100, oversold is better for entry)
        rsi = analysis.technicals.rsi_14
        if rsi is not None:
            if rsi < 30:
                timing_components.append(90)  # Oversold - excellent entry
            elif rsi < 40:
                timing_components.append(75)  # Near oversold - good entry
            elif rsi > 70:
                timing_components.append(20)  # Overbought - poor entry
            elif rsi > 60:
                timing_components.append(35)  # Near overbought - suboptimal
            else:
                timing_components.append(55)  # Neutral
        
        # MACD momentum (bullish crossover = good timing)
        macd = analysis.technicals.macd
        macd_signal = analysis.technicals.macd_signal
        if macd is not None and macd_signal is not None:
            macd_diff = macd - macd_signal
            # Positive and rising MACD is good
            if macd_diff > 0:
                timing_components.append(70)  # Bullish momentum
            else:
                timing_components.append(35)  # Bearish momentum
        
        # Price vs moving averages (below = potential value)
        sma_50 = analysis.technicals.ma_50
        sma_200 = analysis.technicals.ma_200
        current_price = analysis.price.current if hasattr(analysis.price, 'current') else None
        
        if sma_50 and current_price:
            price_to_sma50 = (current_price / sma_50 - 1) * 100  # % from 50 SMA
            # Below 50 SMA but not too far = good entry
            if -10 < price_to_sma50 < -2:
                timing_components.append(75)  # Good pullback entry
            elif price_to_sma50 > 10:
                timing_components.append(30)  # Extended above - risky entry
            elif price_to_sma50 < -15:
                timing_components.append(40)  # Too far below - could be in downtrend
            else:
                timing_components.append(55)  # Near average
        
        # Recent momentum (short-term pullback in uptrend = good entry)
        rolling_1m = analysis.price.rolling_returns.get("1m")
        rolling_3m = analysis.price.rolling_returns.get("3m")
        
        if rolling_1m is not None and rolling_3m is not None:
            # Positive 3m but slight 1m pullback = good entry in uptrend
            if rolling_3m > 0.05 and -0.05 < rolling_1m < 0.02:
                timing_components.append(80)  # Pullback in uptrend
            elif rolling_1m > 0.15:
                timing_components.append(30)  # Extended short-term
            elif rolling_1m < -0.15:
                timing_components.append(35)  # Sharp selloff - catching knife
            else:
                timing_components.append(50)
        
        # Volatility regime (lower volatility = calmer entry)
        volatility = analysis.risk.get("volatility")
        if volatility is not None:
            if volatility < 0.20:
                timing_components.append(70)  # Low vol - stable entry
            elif volatility > 0.40:
                timing_components.append(35)  # High vol - uncertain
            else:
                timing_components.append(50)
        
        return _avg(timing_components) if timing_components else 50