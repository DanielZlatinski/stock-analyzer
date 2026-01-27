SCORE_WEIGHTS = {
    "technical": 0.18,      # Price trends, RSI, MACD
    "fundamental": 0.22,    # ROE, margins, growth
    "valuation": 0.20,      # P/E, PEG, EV/EBITDA
    "risk": 0.12,           # Volatility, beta, drawdown
    "sentiment": 0.08,      # News sentiment
    "momentum": 0.12,       # Recent returns
    "market": 0.08,         # Market & sector conditions
}

# ETF-specific weights (no fundamentals/valuation)
ETF_SCORE_WEIGHTS = {
    "technical": 0.30,      # More weight on technicals for ETFs
    "fundamental": 0.0,     # Not applicable
    "valuation": 0.0,       # Not applicable
    "risk": 0.20,           # Risk is important for ETFs
    "sentiment": 0.10,      # Market sentiment matters
    "momentum": 0.25,       # Momentum/trend following key for ETFs
    "market": 0.15,         # Overall market conditions
}

# Adjusted thresholds to reduce "WATCH" recommendations
# Previous: INVEST >= 70, WATCH >= 45 (WATCH range: 25 points)
# New: INVEST >= 58, WATCH >= 42 (WATCH range: 16 points)
THRESHOLDS = {
    "invest": 58,   # Lowered from 70 - more stocks can be INVEST
    "watch": 42,    # Lowered from 45 - narrower WATCH range
}

# Timing signal thresholds (for entry point quality)
TIMING_THRESHOLDS = {
    "excellent": 75,  # RSI oversold + positive MACD cross + price near support
    "good": 60,       # Some technical indicators favorable
    "fair": 45,       # Mixed signals
    "poor": 0,        # Overbought or adverse conditions
}
