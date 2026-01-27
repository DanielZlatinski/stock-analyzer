import traceback
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify

from core import AnalysisService, DataService, HORIZON_MAP, YFinanceProvider
from core.logging import get_logger
from core.visualization.plotly_charts import (
    calculate_beta,
    fundamentals_trend,
    indices_comparison,
    peer_comparison,
    price_candlestick,
    relative_performance,
    recommendation_waterfall,
    rolling_volatility,
    sentiment_chart,
    volume_chart,
)
from core.visualization.chart_explanations import build_chart_insights


bp = Blueprint("routes", __name__)
logger = get_logger(__name__)

# Popular stock tickers for autocomplete suggestions
POPULAR_TICKERS = {
    # Tech Giants
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc. (Google)",
    "GOOG": "Alphabet Inc. (Google) Class C",
    "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc. (Facebook)",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla Inc.",
    "AMD": "Advanced Micro Devices Inc.",
    "INTC": "Intel Corporation",
    "AVGO": "Broadcom Inc.",
    "ORCL": "Oracle Corporation",
    "CRM": "Salesforce Inc.",
    "ADBE": "Adobe Inc.",
    "NFLX": "Netflix Inc.",
    "CSCO": "Cisco Systems Inc.",
    "IBM": "International Business Machines",
    "QCOM": "Qualcomm Inc.",
    "TXN": "Texas Instruments Inc.",
    "SHOP": "Shopify Inc.",
    "SQ": "Block Inc. (Square)",
    "UBER": "Uber Technologies Inc.",
    "LYFT": "Lyft Inc.",
    "SNAP": "Snap Inc.",
    "PINS": "Pinterest Inc.",
    "ROKU": "Roku Inc.",
    "ZM": "Zoom Video Communications",
    "DOCU": "DocuSign Inc.",
    "PLTR": "Palantir Technologies",
    "SNOW": "Snowflake Inc.",
    "NET": "Cloudflare Inc.",
    "DDOG": "Datadog Inc.",
    "CRWD": "CrowdStrike Holdings",
    "ZS": "Zscaler Inc.",
    "MDB": "MongoDB Inc.",
    "TEAM": "Atlassian Corporation",
    "NOW": "ServiceNow Inc.",
    "WDAY": "Workday Inc.",
    "INTU": "Intuit Inc.",
    "PYPL": "PayPal Holdings Inc.",
    # Finance
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corporation",
    "WFC": "Wells Fargo & Company",
    "GS": "Goldman Sachs Group Inc.",
    "MS": "Morgan Stanley",
    "C": "Citigroup Inc.",
    "V": "Visa Inc.",
    "MA": "Mastercard Inc.",
    "AXP": "American Express Company",
    "BLK": "BlackRock Inc.",
    "SCHW": "Charles Schwab Corporation",
    "USB": "U.S. Bancorp",
    "PNC": "PNC Financial Services",
    "COF": "Capital One Financial",
    "BK": "Bank of New York Mellon",
    # Healthcare
    "JNJ": "Johnson & Johnson",
    "UNH": "UnitedHealth Group Inc.",
    "PFE": "Pfizer Inc.",
    "ABBV": "AbbVie Inc.",
    "MRK": "Merck & Co. Inc.",
    "LLY": "Eli Lilly and Company",
    "TMO": "Thermo Fisher Scientific",
    "ABT": "Abbott Laboratories",
    "BMY": "Bristol-Myers Squibb",
    "AMGN": "Amgen Inc.",
    "GILD": "Gilead Sciences Inc.",
    "MRNA": "Moderna Inc.",
    "CVS": "CVS Health Corporation",
    "ISRG": "Intuitive Surgical Inc.",
    "REGN": "Regeneron Pharmaceuticals",
    "VRTX": "Vertex Pharmaceuticals",
    "BIIB": "Biogen Inc.",
    # Consumer
    "WMT": "Walmart Inc.",
    "COST": "Costco Wholesale Corporation",
    "HD": "Home Depot Inc.",
    "LOW": "Lowe's Companies Inc.",
    "TGT": "Target Corporation",
    "NKE": "Nike Inc.",
    "SBUX": "Starbucks Corporation",
    "MCD": "McDonald's Corporation",
    "KO": "Coca-Cola Company",
    "PEP": "PepsiCo Inc.",
    "PG": "Procter & Gamble Company",
    "DIS": "Walt Disney Company",
    "CMCSA": "Comcast Corporation",
    "ABNB": "Airbnb Inc.",
    "BKNG": "Booking Holdings Inc.",
    "MAR": "Marriott International",
    # Industrial & Energy
    "XOM": "Exxon Mobil Corporation",
    "CVX": "Chevron Corporation",
    "COP": "ConocoPhillips",
    "SLB": "Schlumberger Limited",
    "BA": "Boeing Company",
    "LMT": "Lockheed Martin Corporation",
    "RTX": "RTX Corporation (Raytheon)",
    "CAT": "Caterpillar Inc.",
    "DE": "Deere & Company",
    "UPS": "United Parcel Service",
    "FDX": "FedEx Corporation",
    "HON": "Honeywell International",
    "GE": "General Electric Company",
    "MMM": "3M Company",
    "UNP": "Union Pacific Corporation",
    # Real Estate & Utilities
    "AMT": "American Tower Corporation",
    "PLD": "Prologis Inc.",
    "CCI": "Crown Castle Inc.",
    "EQIX": "Equinix Inc.",
    "SPG": "Simon Property Group",
    "NEE": "NextEra Energy Inc.",
    "DUK": "Duke Energy Corporation",
    "SO": "Southern Company",
    # Telecom
    "T": "AT&T Inc.",
    "VZ": "Verizon Communications",
    "TMUS": "T-Mobile US Inc.",
    # Auto
    "F": "Ford Motor Company",
    "GM": "General Motors Company",
    "RIVN": "Rivian Automotive Inc.",
    "LCID": "Lucid Group Inc.",
    # Major ETFs
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust (NASDAQ-100)",
    "IWM": "iShares Russell 2000 ETF",
    "DIA": "SPDR Dow Jones Industrial Average ETF",
    "VTI": "Vanguard Total Stock Market ETF",
    "VOO": "Vanguard S&P 500 ETF",
    "XLK": "Technology Select Sector SPDR",
    "XLF": "Financial Select Sector SPDR",
    "XLE": "Energy Select Sector SPDR",
    "XLV": "Health Care Select Sector SPDR",
    "ARKK": "ARK Innovation ETF",
}


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            ticker = request.form.get("ticker", "").strip().upper()
            horizon = request.form.get("horizon", "1y")
            interval = request.form.get("interval", "1d")
            if not ticker:
                return render_template("index.html", error="Please enter a ticker.")

            logger.info(f"Processing request for ticker: {ticker}, horizon: {horizon}, interval: {interval}")

            days = HORIZON_MAP.get(horizon, 365)
            end = datetime.utcnow()
            start = end - timedelta(days=days)
            start_str = start.strftime("%Y-%m-%d")
            end_str = end.strftime("%Y-%m-%d")

            logger.info(f"Fetching data for {ticker} from {start_str} to {end_str}")
            provider = YFinanceProvider()
            service = DataService(provider=provider)
            snapshot = service.build_snapshot(ticker, start_str, end_str, interval)
            
            logger.info(f"Running analysis for {ticker}")
            analysis = AnalysisService(service).analyze(snapshot, start_str, end_str, interval)

            logger.info(f"Fetching benchmark prices")
            benchmark_prices = service.get_benchmark_prices(
                snapshot.context.benchmark, start_str, end_str, interval
            )

            logger.info(f"Generating charts for {ticker}")
            charts = {
                "price": price_candlestick(snapshot.price_history, analysis.technicals),
                "volume": volume_chart(snapshot.price_history),
                "relative": relative_performance(snapshot.price_history, benchmark_prices),
                "volatility": rolling_volatility(snapshot.price_history),
                "fundamentals": fundamentals_trend(
                    analysis.fundamentals.time_series, "Fundamental Trends"
                ),
                "peers": peer_comparison(analysis.peers.peer_metrics, ticker),
                "sentiment": sentiment_chart(analysis.sentiment),
                "recommendation": recommendation_waterfall(
                    analysis.recommendation.contributions,
                    analysis.recommendation.score,
                ),
            }
            
            logger.info(f"Building chart insights")
            chart_insights = build_chart_insights(
                ticker=ticker,
                snapshot=snapshot,
                analysis=analysis,
                benchmark_prices=benchmark_prices,
            )

            logger.info(f"Rendering template for {ticker}")
            return render_template(
                "index.html",
                ticker=ticker,
                horizon=horizon,
                interval=interval,
                snapshot=snapshot,
                analysis=analysis,
                charts=charts,
                chart_insights=chart_insights,
            )
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            
            # User-friendly error messages
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
                error_msg = f"Yahoo Finance is rate-limiting requests. Please wait a minute and try again. (This happens when too many requests are made from the same server.)"
            elif "unable to fetch" in error_str:
                error_msg = f"Unable to fetch data for {ticker}. Yahoo Finance may be temporarily unavailable. Please try again in a few minutes."
            else:
                error_msg = f"Error processing {ticker}: {str(e)}"
            
            return render_template("index.html", error=error_msg, horizon=horizon, interval=interval)

    return render_template("index.html", horizon="1y", interval="1d")


@bp.route("/test")
def test():
    """Simple test endpoint to verify the app is working"""
    try:
        import sys
        import os
        info = {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "project_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        }
        # Test imports
        try:
            from core import DataService, YFinanceProvider
            info["core_imports"] = "OK"
        except Exception as e:
            info["core_imports"] = f"FAILED: {str(e)}"
        
        try:
            import yfinance
            info["yfinance"] = "OK"
        except Exception as e:
            info["yfinance"] = f"FAILED: {str(e)}"
        
        try:
            import plotly
            info["plotly"] = "OK"
        except Exception as e:
            info["plotly"] = f"FAILED: {str(e)}"
        
        return f"<pre>{info}</pre>"
    except Exception as e:
        return f"<pre>Error: {str(e)}\n{traceback.format_exc()}</pre>"


def fuzzy_match(query, text, threshold=0.6):
    """Simple fuzzy matching - returns True if query is similar enough to text"""
    query = query.lower()
    text = text.lower()
    
    # Exact substring match
    if query in text:
        return True, 1.0
    
    # Check if all characters of query appear in order in text
    q_idx = 0
    for char in text:
        if q_idx < len(query) and char == query[q_idx]:
            q_idx += 1
    if q_idx == len(query):
        return True, 0.9
    
    # Simple character-based similarity for short queries
    if len(query) <= 4:
        # Allow one character difference for short strings
        matches = sum(1 for c in query if c in text)
        similarity = matches / len(query)
        if similarity >= threshold:
            return True, similarity
    
    # Levenshtein-like distance for longer queries
    if len(query) >= 3:
        # Check if query matches start of any word in text
        words = text.replace('(', ' ').replace(')', ' ').replace('.', ' ').split()
        for word in words:
            if word.startswith(query[:min(3, len(query))]):
                return True, 0.8
            # Allow 1 typo for words of similar length
            if abs(len(word) - len(query)) <= 2:
                diff = sum(1 for a, b in zip(query, word) if a != b)
                diff += abs(len(word) - len(query))
                if diff <= 2:
                    return True, 0.7
    
    return False, 0.0


@bp.route("/api/search")
def search_tickers():
    """API endpoint for ticker search with autocomplete suggestions and fuzzy matching"""
    query = request.args.get("q", "").strip()
    query_upper = query.upper()
    
    if not query or len(query) < 1:
        return jsonify({"results": []})
    
    results = []
    
    # Search in our popular tickers list
    for ticker, name in POPULAR_TICKERS.items():
        score = 0
        match_type = None
        
        # Exact ticker match (highest priority)
        if query_upper == ticker:
            score = 100
            match_type = "exact"
        # Ticker starts with query
        elif ticker.startswith(query_upper):
            score = 90
            match_type = "ticker_prefix"
        # Query is substring of ticker
        elif query_upper in ticker:
            score = 80
            match_type = "ticker_substring"
        # Exact name word match
        elif query.lower() in name.lower().split():
            score = 75
            match_type = "name_word"
        # Name contains query
        elif query.lower() in name.lower():
            score = 70
            match_type = "name_substring"
        else:
            # Fuzzy matching
            ticker_match, ticker_sim = fuzzy_match(query_upper, ticker)
            name_match, name_sim = fuzzy_match(query, name)
            
            if ticker_match and ticker_sim >= 0.7:
                score = int(60 * ticker_sim)
                match_type = "ticker_fuzzy"
            elif name_match and name_sim >= 0.6:
                score = int(50 * name_sim)
                match_type = "name_fuzzy"
        
        if score > 0:
            results.append({
                "ticker": ticker,
                "name": name,
                "score": score,
                "match_type": match_type
            })
    
    # Sort by score (descending), then by ticker length
    results.sort(key=lambda x: (-x["score"], len(x["ticker"]), x["ticker"]))
    
    # Limit results
    results = results[:10]
    
    # Remove score from response (internal use only)
    for r in results:
        del r["score"]
    
    return jsonify({"results": results})


@bp.route("/api/chart-data")
def get_chart_data():
    """API endpoint to get updated chart data for a specific period"""
    import yfinance as yf
    
    ticker = request.args.get("ticker", "").strip().upper()
    period = request.args.get("period", "1y")
    chart_type = request.args.get("type", "price")  # price, volume, relative, volatility
    
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400
    
    # Map our period to yfinance period format
    yf_period_map = {
        "1d": "5d",      # Use 5 days of data for "1 day" view (more reliable)
        "5d": "5d",
        "1m": "1mo",
        "6m": "6mo",
        "1y": "1y",
        "5y": "5y",
        "max": "max"
    }
    
    yf_period = yf_period_map.get(period, "1y")
    interval = "1d"  # Use daily data for all periods (most reliable)
    
    try:
        # Fetch data using yfinance directly with period parameter
        yf_ticker = yf.Ticker(ticker)
        hist = yf_ticker.history(period=yf_period, interval=interval)
        
        if hist is None or hist.empty:
            return jsonify({"error": f"No data found for {ticker}"}), 404
        
        # Convert to PricePoint list
        from core.models import PricePoint
        price_history = []
        for idx, row in hist.iterrows():
            try:
                price_history.append(
                    PricePoint(
                        date=idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                        open=float(row.get("Open", 0) or 0),
                        high=float(row.get("High", 0) or 0),
                        low=float(row.get("Low", 0) or 0),
                        close=float(row.get("Close", 0) or 0),
                        volume=float(row.get("Volume", 0) or 0),
                    )
                )
            except Exception:
                continue
        
        if not price_history:
            return jsonify({"error": f"No valid data for {ticker}"}), 404
        
        # Get benchmark for relative performance
        provider = YFinanceProvider()
        context = provider.get_ticker_context(ticker)
        benchmark = context.benchmark
        
        benchmark_history = []
        if chart_type == "relative":
            bench_ticker = yf.Ticker(benchmark)
            bench_hist = bench_ticker.history(period=yf_period, interval=interval)
            if bench_hist is not None and not bench_hist.empty:
                for idx, row in bench_hist.iterrows():
                    try:
                        benchmark_history.append(
                            PricePoint(
                                date=idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                                open=float(row.get("Open", 0) or 0),
                                high=float(row.get("High", 0) or 0),
                                low=float(row.get("Low", 0) or 0),
                                close=float(row.get("Close", 0) or 0),
                                volume=float(row.get("Volume", 0) or 0),
                            )
                        )
                    except Exception:
                        continue
        
        # Generate requested chart
        chart_html = ""
        if chart_type == "price":
            # Get technicals for price chart
            from core.analytics.technicals import build_technical_indicators
            technicals = build_technical_indicators(price_history)
            chart_html = price_candlestick(price_history, technicals)
        elif chart_type == "volume":
            chart_html = volume_chart(price_history)
        elif chart_type == "relative":
            chart_html = relative_performance(price_history, benchmark_history)
        elif chart_type == "volatility":
            # Rolling volatility needs at least 20 data points
            if len(price_history) < 20:
                chart_html = "<div style='padding: 40px; text-align: center; color: #64748b;'>Not enough data for volatility calculation (need 20+ days)</div>"
            else:
                chart_html = rolling_volatility(price_history)
        elif chart_type == "indices":
            # Major indices comparison chart
            indices = {
                "S&P 500": "SPY",
                "NASDAQ": "QQQ",
                "DOW": "DIA"
            }
            
            indices_data = {}
            for index_name, index_ticker in indices.items():
                try:
                    idx_yf = yf.Ticker(index_ticker)
                    idx_hist = idx_yf.history(period=yf_period, interval=interval)
                    if idx_hist is not None and not idx_hist.empty:
                        idx_prices = []
                        for idx, row in idx_hist.iterrows():
                            try:
                                idx_prices.append(
                                    PricePoint(
                                        date=idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                                        open=float(row.get("Open", 0) or 0),
                                        high=float(row.get("High", 0) or 0),
                                        low=float(row.get("Low", 0) or 0),
                                        close=float(row.get("Close", 0) or 0),
                                        volume=float(row.get("Volume", 0) or 0),
                                    )
                                )
                            except Exception:
                                continue
                        if idx_prices:
                            indices_data[index_name] = idx_prices
                except Exception as e:
                    logger.warning(f"Failed to fetch {index_name}: {e}")
            
            chart_html = indices_comparison(price_history, indices_data, ticker)
        elif chart_type == "fundamentals":
            # Fundamentals chart - uses financial statement data
            from core.visualization.plotly_charts import fundamentals_trend
            
            # Map period to years of data
            years_map = {"1y": 1, "3y": 3, "5y": 5, "10y": 10, "max": 20}
            years = years_map.get(period, 5)
            
            # Get financial data from yfinance
            financials = yf_ticker.financials
            
            if financials is not None and not financials.empty:
                # Build time series for chart
                time_series = {}
                
                # Get revenue
                if "Total Revenue" in financials.index:
                    revenue_data = financials.loc["Total Revenue"].dropna()
                    revenue_dict = {str(date)[:10]: float(val) / 1e9 for date, val in revenue_data.items()}
                    # Filter by years
                    sorted_dates = sorted(revenue_dict.keys(), reverse=True)[:years]
                    time_series["Revenue ($B)"] = {d: revenue_dict[d] for d in sorted_dates}
                
                # Get net income
                if "Net Income" in financials.index:
                    income_data = financials.loc["Net Income"].dropna()
                    income_dict = {str(date)[:10]: float(val) / 1e9 for date, val in income_data.items()}
                    sorted_dates = sorted(income_dict.keys(), reverse=True)[:years]
                    time_series["Net Income ($B)"] = {d: income_dict[d] for d in sorted_dates}
                
                # Get cash flow data
                cash_flow = yf_ticker.cashflow
                if cash_flow is not None and not cash_flow.empty:
                    if "Free Cash Flow" in cash_flow.index:
                        fcf_data = cash_flow.loc["Free Cash Flow"].dropna()
                        fcf_dict = {str(date)[:10]: float(val) / 1e9 for date, val in fcf_data.items()}
                        sorted_dates = sorted(fcf_dict.keys(), reverse=True)[:years]
                        time_series["Free Cash Flow ($B)"] = {d: fcf_dict[d] for d in sorted_dates}
                
                chart_html = fundamentals_trend(time_series, "Financial Trends")
            else:
                chart_html = "<p style='padding: 40px; text-align: center; color: #64748b;'>No financial data available</p>"
        else:
            return jsonify({"error": f"Unknown chart type: {chart_type}"}), 400
        
        return jsonify({
            "html": chart_html,
            "ticker": ticker,
            "period": period,
            "chart_type": chart_type
        })
        
    except Exception as e:
        logger.error(f"Error getting chart data for {ticker}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@bp.route("/api/validate-ticker")
def validate_ticker():
    """API endpoint to validate a ticker exists and get basic info"""
    ticker = request.args.get("ticker", "").strip().upper()
    
    if not ticker:
        return jsonify({"valid": False, "error": "No ticker provided"})
    
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.info
        
        # Check if we got valid data
        if not info or info.get("regularMarketPrice") is None:
            # Try to get historical data as backup validation
            hist = t.history(period="5d")
            if hist.empty:
                return jsonify({"valid": False, "error": f"Ticker '{ticker}' not found"})
        
        company_name = info.get("shortName") or info.get("longName") or ticker
        return jsonify({
            "valid": True,
            "ticker": ticker,
            "name": company_name,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        })
    except Exception as e:
        logger.error(f"Error validating ticker {ticker}: {e}")
        return jsonify({"valid": False, "error": str(e)})


@bp.route("/api/options-data")
def get_options_data():
    """API endpoint to get options analysis for a ticker"""
    ticker = request.args.get("ticker", "").strip().upper()
    
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400
    
    try:
        from core.analytics.options import analyze_options
        from core.visualization.plotly_charts import options_volume_chart, options_oi_chart
        
        # Get options analysis
        options_data = analyze_options(ticker)
        
        if not options_data.get("available"):
            return jsonify({
                "available": False,
                "message": options_data.get("message", "No options data available"),
            })
        
        # Generate charts
        volume_chart_html = options_volume_chart(options_data)
        oi_chart_html = options_oi_chart(options_data)
        
        return jsonify({
            "available": True,
            "data": options_data,
            "volume_chart_html": volume_chart_html,
            "oi_chart_html": oi_chart_html,
        })
        
    except Exception as e:
        logger.error(f"Error getting options data for {ticker}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@bp.route("/api/market-sentiment")
def get_market_sentiment():
    """API endpoint to get overall market sentiment data"""
    try:
        from core.analytics.market_sentiment import analyze_market_sentiment, get_sector_performance
        from core.visualization.plotly_charts import sentiment_gauge, sector_heatmap
        
        # Get market sentiment analysis
        sentiment_data = analyze_market_sentiment()
        
        # Generate gauge chart
        gauge_html = sentiment_gauge(
            sentiment_data["score"],
            sentiment_data["sentiment"]
        )
        
        # Get sector performance
        sectors = get_sector_performance()
        sector_chart_html = sector_heatmap(sectors)
        
        return jsonify({
            "sentiment": sentiment_data,
            "gauge_html": gauge_html,
            "sector_chart_html": sector_chart_html,
            "sectors": sectors,
        })
        
    except Exception as e:
        logger.error(f"Error getting market sentiment: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
