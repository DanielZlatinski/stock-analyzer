SCORE_WEIGHTS = {
    "technical": 0.15,      # Price trends, RSI, MACD
    "momentum": 0.10,       # Recent returns
    "fundamental": 0.20,    # ROE, margins, growth
    "valuation": 0.18,      # P/E, PEG, EV/EBITDA
    "peers": 0.07,          # Peer comparison rankings
    "market": 0.08,         # Market & sector conditions
    "sentiment": 0.07,      # News sentiment
    "risk": 0.15,           # Volatility, beta, drawdown
}

# ETF-specific weights (no fundamentals/valuation/peers)
ETF_SCORE_WEIGHTS = {
    "technical": 0.28,      # More weight on technicals for ETFs
    "momentum": 0.22,       # Momentum/trend following key for ETFs
    "fundamental": 0.0,     # Not applicable
    "valuation": 0.0,       # Not applicable
    "peers": 0.0,           # Not applicable for ETFs
    "market": 0.15,         # Overall market conditions
    "sentiment": 0.10,      # Market sentiment matters
    "risk": 0.25,           # Risk is important for ETFs
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
