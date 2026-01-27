"""
Options analytics for analyzing options chain data and sentiment.
"""
import yfinance as yf
from datetime import datetime, timedelta


def analyze_options(ticker):
    """
    Analyze options data for a given ticker.
    Returns options sentiment analysis including Put/Call ratios, volume, and open interest.
    """
    try:
        yf_ticker = yf.Ticker(ticker)
        
        # Get available expiration dates
        expirations = yf_ticker.options
        if not expirations:
            return {
                "available": False,
                "message": "No options data available for this ticker",
            }
        
        # Get the nearest expiration (typically most liquid)
        nearest_exp = expirations[0]
        
        # Also get a monthly expiration if available (usually 3-4 weeks out)
        monthly_exp = None
        for exp in expirations:
            exp_date = datetime.strptime(exp, "%Y-%m-%d")
            days_to_exp = (exp_date - datetime.now()).days
            if 20 <= days_to_exp <= 45:
                monthly_exp = exp
                break
        
        if not monthly_exp:
            monthly_exp = expirations[1] if len(expirations) > 1 else nearest_exp
        
        # Get options chain for nearest expiration
        opt_chain = yf_ticker.option_chain(nearest_exp)
        calls = opt_chain.calls
        puts = opt_chain.puts
        
        if calls.empty and puts.empty:
            return {
                "available": False,
                "message": "Options chain data is empty",
            }
        
        # Calculate key metrics
        # Volume
        total_call_volume = int(calls["volume"].sum()) if "volume" in calls.columns else 0
        total_put_volume = int(puts["volume"].sum()) if "volume" in puts.columns else 0
        total_volume = total_call_volume + total_put_volume
        
        # Open Interest
        total_call_oi = int(calls["openInterest"].sum()) if "openInterest" in calls.columns else 0
        total_put_oi = int(puts["openInterest"].sum()) if "openInterest" in puts.columns else 0
        total_oi = total_call_oi + total_put_oi
        
        # Put/Call Ratios
        pcr_volume = round(total_put_volume / total_call_volume, 2) if total_call_volume > 0 else None
        pcr_oi = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else None
        
        # Determine sentiment based on PCR
        # PCR < 0.7 = Bullish (more calls), PCR > 1.0 = Bearish (more puts)
        if pcr_volume:
            if pcr_volume < 0.7:
                volume_sentiment = "Bullish"
                volume_sentiment_color = "bullish"
            elif pcr_volume < 1.0:
                volume_sentiment = "Neutral"
                volume_sentiment_color = "neutral"
            else:
                volume_sentiment = "Bearish"
                volume_sentiment_color = "bearish"
        else:
            volume_sentiment = "Unknown"
            volume_sentiment_color = "neutral"
        
        if pcr_oi:
            if pcr_oi < 0.7:
                oi_sentiment = "Bullish"
                oi_sentiment_color = "bullish"
            elif pcr_oi < 1.0:
                oi_sentiment = "Neutral"
                oi_sentiment_color = "neutral"
            else:
                oi_sentiment = "Bearish"
                oi_sentiment_color = "bearish"
        else:
            oi_sentiment = "Unknown"
            oi_sentiment_color = "neutral"
        
        # Get current stock price for context
        current_price = None
        try:
            hist = yf_ticker.history(period="1d")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])
        except:
            pass
        
        # Find most active strikes
        top_call_strikes = []
        top_put_strikes = []
        
        if not calls.empty and "volume" in calls.columns:
            top_calls = calls.nlargest(5, "volume")[["strike", "volume", "openInterest", "lastPrice"]]
            for _, row in top_calls.iterrows():
                top_call_strikes.append({
                    "strike": float(row["strike"]),
                    "volume": int(row["volume"]) if row["volume"] else 0,
                    "oi": int(row["openInterest"]) if row["openInterest"] else 0,
                    "price": float(row["lastPrice"]) if row["lastPrice"] else 0,
                })
        
        if not puts.empty and "volume" in puts.columns:
            top_puts = puts.nlargest(5, "volume")[["strike", "volume", "openInterest", "lastPrice"]]
            for _, row in top_puts.iterrows():
                top_put_strikes.append({
                    "strike": float(row["strike"]),
                    "volume": int(row["volume"]) if row["volume"] else 0,
                    "oi": int(row["openInterest"]) if row["openInterest"] else 0,
                    "price": float(row["lastPrice"]) if row["lastPrice"] else 0,
                })
        
        # Implied Move calculation (simplified)
        atm_call_price = 0
        atm_put_price = 0
        if current_price and not calls.empty and not puts.empty:
            # Find at-the-money options
            calls_sorted = calls.iloc[(calls["strike"] - current_price).abs().argsort()[:1]]
            puts_sorted = puts.iloc[(puts["strike"] - current_price).abs().argsort()[:1]]
            
            if not calls_sorted.empty:
                atm_call_price = float(calls_sorted["lastPrice"].iloc[0]) if calls_sorted["lastPrice"].iloc[0] else 0
            if not puts_sorted.empty:
                atm_put_price = float(puts_sorted["lastPrice"].iloc[0]) if puts_sorted["lastPrice"].iloc[0] else 0
        
        implied_move = None
        implied_move_pct = None
        if current_price and (atm_call_price + atm_put_price) > 0:
            implied_move = atm_call_price + atm_put_price
            implied_move_pct = round((implied_move / current_price) * 100, 1)
        
        return {
            "available": True,
            "expiration": nearest_exp,
            "expirations_available": len(expirations),
            "current_price": round(current_price, 2) if current_price else None,
            "volume": {
                "calls": total_call_volume,
                "puts": total_put_volume,
                "total": total_volume,
                "pcr": pcr_volume,
                "sentiment": volume_sentiment,
                "sentiment_color": volume_sentiment_color,
            },
            "open_interest": {
                "calls": total_call_oi,
                "puts": total_put_oi,
                "total": total_oi,
                "pcr": pcr_oi,
                "sentiment": oi_sentiment,
                "sentiment_color": oi_sentiment_color,
            },
            "implied_move": {
                "dollars": round(implied_move, 2) if implied_move else None,
                "percent": implied_move_pct,
            },
            "top_call_strikes": top_call_strikes,
            "top_put_strikes": top_put_strikes,
        }
        
    except Exception as e:
        return {
            "available": False,
            "message": f"Error analyzing options: {str(e)}",
        }
