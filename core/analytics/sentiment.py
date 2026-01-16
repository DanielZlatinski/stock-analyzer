from core.analysis_models import SentimentSummary


# Expanded word lists for better sentiment detection
POSITIVE_WORDS = {
    # Performance
    "beat", "beats", "beating", "exceeded", "exceeds", "surpass", "surpassed",
    "outperform", "outperformed", "outperforms",
    # Growth
    "growth", "grow", "grows", "growing", "expand", "expansion", "expanding",
    "surge", "surges", "surging", "soar", "soars", "soaring", "jump", "jumps",
    "rise", "rises", "rising", "gain", "gains", "rally", "rallies",
    # Strength
    "strong", "stronger", "strongest", "record", "high", "higher", "highest",
    "robust", "solid", "resilient",
    # Positive actions
    "upgrade", "upgrades", "upgraded", "raise", "raises", "raised", "boost",
    "boosted", "boosts", "accelerate", "accelerates",
    # Sentiment
    "positive", "bullish", "optimistic", "confident", "upbeat",
    # Success
    "success", "successful", "win", "wins", "winning", "breakthrough",
    "innovation", "innovative", "launch", "launches",
    # Financials
    "profit", "profits", "profitable", "dividend", "buyback", "approved",
}

NEGATIVE_WORDS = {
    # Performance
    "miss", "misses", "missed", "disappoint", "disappoints", "disappointed",
    "underperform", "underperformed", "underperforms",
    # Decline
    "decline", "declines", "declining", "drop", "drops", "dropping",
    "fall", "falls", "falling", "fell", "plunge", "plunges", "tumble",
    "sink", "sinks", "slump", "slumps", "crash", "crashes",
    # Weakness
    "weak", "weaker", "weakest", "low", "lower", "lowest", "poor",
    "soft", "sluggish",
    # Negative actions
    "downgrade", "downgrades", "downgraded", "cut", "cuts", "cutting",
    "reduce", "reduces", "reduced", "slash", "slashes",
    # Sentiment
    "negative", "bearish", "pessimistic", "worried", "concerns", "concern",
    "warning", "warns", "warned", "caution", "cautious", "fear", "fears",
    # Problems
    "loss", "losses", "losing", "fail", "fails", "failed", "failure",
    "lawsuit", "investigation", "probe", "recall", "recalls",
    "layoff", "layoffs", "restructuring", "bankruptcy",
    # Risk
    "risk", "risks", "risky", "volatile", "uncertainty", "uncertain",
    "delay", "delays", "delayed",
}

NEUTRAL_FILTER = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "has", "have", "had", "will", "would", "could", "should", "may", "might",
}


def _score_text(text):
    """Score text sentiment from -1 to 1."""
    if not text:
        return 0
    tokens = [token.strip(".,!?:;\"'()[]").lower() for token in text.split()]
    tokens = [t for t in tokens if t and t not in NEUTRAL_FILTER]
    
    positive_count = sum(1 for word in tokens if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in tokens if word in NEGATIVE_WORDS)
    
    if positive_count == 0 and negative_count == 0:
        return 0
    
    # Return score between -1 and 1
    total = positive_count + negative_count
    return round((positive_count - negative_count) / total, 2)


def _classify_sentiment(score):
    """Classify sentiment score into category."""
    if score >= 0.3:
        return "positive"
    elif score <= -0.3:
        return "negative"
    return "neutral"


def build_sentiment_summary(news_items, social_posts):
    """Build comprehensive sentiment summary from news and social data."""
    # Score each news item
    scored_items = []
    for item in news_items[:100]:  # Limit to 100 items for performance
        score = _score_text(item.title)
        scored_items.append({
            "title": item.title,
            "publisher": item.publisher,
            "url": item.url,
            "published_at": item.published_at,
            "score": score,
            "sentiment": _classify_sentiment(score),
        })
    
    # Calculate aggregate scores
    scores = [item["score"] for item in scored_items]
    headline_volume = len(scores)
    headline_score = round(sum(scores) / headline_volume, 2) if scores else None
    
    # Count by sentiment
    positive_count = sum(1 for item in scored_items if item["sentiment"] == "positive")
    negative_count = sum(1 for item in scored_items if item["sentiment"] == "negative")
    neutral_count = sum(1 for item in scored_items if item["sentiment"] == "neutral")
    
    # Determine overall sentiment
    if headline_score is not None:
        if headline_score >= 0.2:
            overall_sentiment = "Bullish"
            sentiment_description = "Recent news coverage is predominantly positive."
        elif headline_score <= -0.2:
            overall_sentiment = "Bearish"
            sentiment_description = "Recent news coverage is predominantly negative."
        else:
            overall_sentiment = "Mixed"
            sentiment_description = "Recent news coverage shows mixed sentiment."
    else:
        overall_sentiment = "No Data"
        sentiment_description = "Insufficient news data for sentiment analysis."
    
    social_volume = len(social_posts)
    
    return SentimentSummary(
        headline_score=headline_score,
        headline_volume=headline_volume,
        social_volume=social_volume,
        scored_items=scored_items,
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count,
        overall_sentiment=overall_sentiment,
        sentiment_description=sentiment_description,
    )
