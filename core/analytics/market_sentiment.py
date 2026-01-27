"""
Market-level sentiment analysis for macro market conditions.
Analyzes overall market sentiment based on indices performance and market news.
"""
import yfinance as yf
from datetime import datetime, timedelta


# Market sentiment keywords
BULLISH_KEYWORDS = {
    "rally", "rallies", "surge", "surges", "boom", "bull", "bullish",
    "record high", "all-time high", "breakout", "recovery", "rebound",
    "optimism", "optimistic", "confidence", "strong", "growth",
    "beat", "beats", "exceeded", "outperform", "upgrade", "buy",
}

BEARISH_KEYWORDS = {
    "crash", "crashes", "plunge", "plunges", "bear", "bearish",
    "correction", "selloff", "sell-off", "decline", "recession",
    "fear", "panic", "warning", "risk", "concern", "volatile",
    "miss", "misses", "downgrade", "sell", "weak", "uncertainty",
    "tariff", "tariffs", "trade war", "inflation", "rate hike",
}


def analyze_market_sentiment():
    """
    Analyze overall market sentiment based on:
    1. Recent performance of major indices
    2. Market volatility (VIX)
    3. Market breadth indicators
    """
    try:
        # Fetch data for major indices
        indices = {
            "SPY": "S&P 500",
            "QQQ": "NASDAQ 100",
            "DIA": "Dow Jones",
            "IWM": "Russell 2000",
        }
        
        # Get VIX for fear gauge
        vix_ticker = yf.Ticker("^VIX")
        vix_data = vix_ticker.history(period="5d")
        current_vix = float(vix_data["Close"].iloc[-1]) if not vix_data.empty else None
        vix_change = None
        if len(vix_data) >= 2:
            vix_change = ((vix_data["Close"].iloc[-1] / vix_data["Close"].iloc[0]) - 1) * 100
        
        # Analyze each index
        index_performance = {}
        for ticker, name in indices.items():
            try:
                yf_ticker = yf.Ticker(ticker)
                hist = yf_ticker.history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    current = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[0])
                    change_pct = ((current / prev) - 1) * 100
                    
                    # Get 1-month performance
                    hist_1m = yf_ticker.history(period="1mo")
                    monthly_change = None
                    if not hist_1m.empty and len(hist_1m) >= 2:
                        monthly_change = ((hist_1m["Close"].iloc[-1] / hist_1m["Close"].iloc[0]) - 1) * 100
                    
                    index_performance[name] = {
                        "ticker": ticker,
                        "current": current,
                        "weekly_change": round(change_pct, 2),
                        "monthly_change": round(monthly_change, 2) if monthly_change else None,
                        "trend": "up" if change_pct > 0 else "down",
                    }
            except Exception:
                continue
        
        # Calculate overall market score (-100 to +100)
        weekly_changes = [p["weekly_change"] for p in index_performance.values() if p.get("weekly_change")]
        avg_weekly = sum(weekly_changes) / len(weekly_changes) if weekly_changes else 0
        
        # VIX component: high VIX = bearish
        vix_score = 0
        vix_level = "Normal"
        if current_vix:
            if current_vix < 15:
                vix_score = 20  # Low fear = bullish
                vix_level = "Low (Complacent)"
            elif current_vix < 20:
                vix_score = 10
                vix_level = "Normal"
            elif current_vix < 25:
                vix_score = -10
                vix_level = "Elevated"
            elif current_vix < 30:
                vix_score = -20
                vix_level = "High"
            else:
                vix_score = -30  # High fear = bearish
                vix_level = "Extreme Fear"
        
        # Combined score
        price_score = min(max(avg_weekly * 5, -50), 50)  # Cap at ±50
        market_score = price_score + vix_score
        market_score = min(max(market_score, -100), 100)  # Cap at ±100
        
        # Determine sentiment classification
        if market_score >= 30:
            sentiment = "Bullish"
            sentiment_color = "bullish"
            description = "Market conditions are favorable with positive momentum across major indices."
        elif market_score >= 10:
            sentiment = "Slightly Bullish"
            sentiment_color = "slightly-bullish"
            description = "Market shows modest positive momentum with mixed signals."
        elif market_score >= -10:
            sentiment = "Neutral"
            sentiment_color = "neutral"
            description = "Market is consolidating with no clear directional bias."
        elif market_score >= -30:
            sentiment = "Slightly Bearish"
            sentiment_color = "slightly-bearish"
            description = "Market shows weakness with some caution warranted."
        else:
            sentiment = "Bearish"
            sentiment_color = "bearish"
            description = "Market conditions are challenging with significant downward pressure."
        
        # Get market news
        market_news = get_market_news()
        
        return {
            "score": round(market_score, 1),
            "sentiment": sentiment,
            "sentiment_color": sentiment_color,
            "description": description,
            "vix": {
                "current": round(current_vix, 2) if current_vix else None,
                "change": round(vix_change, 2) if vix_change else None,
                "level": vix_level,
            },
            "indices": index_performance,
            "news": market_news,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        
    except Exception as e:
        return {
            "score": 0,
            "sentiment": "Unknown",
            "sentiment_color": "neutral",
            "description": f"Unable to analyze market sentiment: {str(e)}",
            "vix": None,
            "indices": {},
            "news": [],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }


def get_market_news():
    """Fetch recent market-wide news headlines."""
    try:
        # Use SPY as proxy for market news
        spy = yf.Ticker("SPY")
        news_data = spy.news if hasattr(spy, 'news') else []
        
        # Handle both list and dict formats (yfinance API changes)
        if isinstance(news_data, dict):
            news = news_data.get('news', [])[:10]
        elif isinstance(news_data, list):
            news = news_data[:10]
        else:
            news = []
        
        headlines = []
        for item in news:
            # Handle nested 'content' structure (newer yfinance versions)
            content = item.get("content", item)  # Fallback to item itself if no content key
            
            # Extract title - handle multiple possible locations
            title = (
                content.get("title") or 
                item.get("title") or 
                content.get("headline") or 
                item.get("headline") or 
                ""
            )
            
            # Extract publisher - handle nested provider structure
            provider = content.get("provider", {})
            publisher = (
                provider.get("displayName") if isinstance(provider, dict) else
                content.get("publisher") or 
                item.get("publisher") or 
                item.get("source") or 
                "Market News"
            )
            
            # Extract link - handle nested URL structures
            click_url = content.get("clickThroughUrl", {})
            canonical_url = content.get("canonicalUrl", {})
            link = (
                click_url.get("url") if isinstance(click_url, dict) else
                canonical_url.get("url") if isinstance(canonical_url, dict) else
                content.get("link") or
                item.get("link") or 
                item.get("url") or 
                "#"
            )
            
            # Get publish time - handle different formats
            pub_time = (
                content.get("pubDate") or
                content.get("displayTime") or
                item.get("providerPublishTime") or 
                item.get("publishedAt") or 
                item.get("publish_time")
            )
            published_str = ""
            if pub_time:
                try:
                    if isinstance(pub_time, (int, float)):
                        published_str = datetime.fromtimestamp(pub_time).strftime("%b %d, %H:%M")
                    elif isinstance(pub_time, str):
                        # Parse ISO format date string
                        if "T" in pub_time:
                            dt = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
                            published_str = dt.strftime("%b %d, %H:%M")
                        else:
                            published_str = pub_time[:16]
                except:
                    pass
            
            if not title:
                continue
                
            # Score the headline
            title_lower = title.lower()
            bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in title_lower)
            bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in title_lower)
            
            if bullish_count > bearish_count:
                sentiment = "positive"
            elif bearish_count > bullish_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            headlines.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "sentiment": sentiment,
                "published": published_str,
            })
        
        return headlines
    except Exception as e:
        print(f"Error fetching market news: {e}")
        return []


def get_sector_performance():
    """Get performance of major sector ETFs."""
    sectors = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLV": "Healthcare",
        "XLE": "Energy",
        "XLI": "Industrials",
        "XLY": "Consumer Disc.",
        "XLP": "Consumer Staples",
        "XLU": "Utilities",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLC": "Communication",
    }
    
    sector_data = []
    try:
        for ticker, name in sectors.items():
            try:
                yf_ticker = yf.Ticker(ticker)
                hist = yf_ticker.history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    current = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[0])
                    change_pct = ((current / prev) - 1) * 100
                    
                    # Get 1-month change
                    hist_1m = yf_ticker.history(period="1mo")
                    monthly_change = None
                    if not hist_1m.empty and len(hist_1m) >= 2:
                        monthly_change = ((hist_1m["Close"].iloc[-1] / hist_1m["Close"].iloc[0]) - 1) * 100
                    
                    sector_data.append({
                        "ticker": ticker,
                        "name": name,
                        "weekly_change": round(change_pct, 2),
                        "monthly_change": round(monthly_change, 2) if monthly_change else None,
                        "trend": "up" if change_pct > 0 else "down",
                    })
            except Exception:
                continue
        
        # Sort by weekly change
        sector_data.sort(key=lambda x: x["weekly_change"], reverse=True)
        
    except Exception:
        pass
    
    return sector_data
