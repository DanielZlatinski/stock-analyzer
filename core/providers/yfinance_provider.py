from datetime import datetime, timedelta
import logging
import time
import requests

import yfinance as yf
import pandas as pd

from core.config import DEFAULT_BENCHMARK, SECTOR_ETF_MAP, FINNHUB_API_KEY
from core.models import NewsItem, PricePoint, SocialPost, TickerContext
from core.providers.base import DataProvider

logger = logging.getLogger("research_terminal")

FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/company-news"


# Fallback peers by industry/sector when yfinance doesn't provide them
INDUSTRY_PEERS = {
    # Tech - Software
    "Software—Infrastructure": ["MSFT", "ORCL", "CRM", "NOW", "ADBE", "INTU"],
    "Software—Application": ["MSFT", "CRM", "ADBE", "INTU", "WDAY", "TEAM"],
    # Tech - Hardware/Semiconductors
    "Semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "MU"],
    "Consumer Electronics": ["AAPL", "SONY", "DELL", "HPQ", "LOGI"],
    "Computer Hardware": ["AAPL", "DELL", "HPQ", "LNVGY"],
    # Finance
    "Banks—Diversified": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
    "Banks—Regional": ["USB", "PNC", "TFC", "FITB", "KEY"],
    "Asset Management": ["BLK", "BX", "KKR", "APO", "TROW"],
    "Insurance—Diversified": ["BRK-B", "AIG", "MET", "PRU", "ALL"],
    # Healthcare
    "Drug Manufacturers—General": ["JNJ", "PFE", "MRK", "ABBV", "LLY", "BMY"],
    "Biotechnology": ["AMGN", "GILD", "REGN", "VRTX", "BIIB", "MRNA"],
    "Medical Devices": ["MDT", "ABT", "SYK", "BSX", "EW", "ISRG"],
    # Consumer
    "Internet Retail": ["AMZN", "EBAY", "ETSY", "W", "CHWY"],
    "Specialty Retail": ["HD", "LOW", "TJX", "ROST", "BBY"],
    "Restaurants": ["MCD", "SBUX", "CMG", "DRI", "YUM", "DENN"],
    "Beverages—Non-Alcoholic": ["KO", "PEP", "MNST", "KDP"],
    # Industrial
    "Aerospace & Defense": ["BA", "LMT", "RTX", "NOC", "GD", "HII"],
    "Auto Manufacturers": ["TSLA", "F", "GM", "TM", "HMC", "RIVN"],
    # Energy
    "Oil & Gas Integrated": ["XOM", "CVX", "SHEL", "BP", "TTE", "COP"],
    # Communication
    "Internet Content & Information": ["GOOGL", "META", "SNAP", "PINS", "TWTR"],
    "Entertainment": ["NFLX", "DIS", "WBD", "PARA", "CMCSA"],
    "Telecom Services": ["T", "VZ", "TMUS"],
}

SECTOR_LEADERS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "CRM", "AMD", "ADBE", "ORCL"],
    "Healthcare": ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "AMGN"],
    "Financial Services": ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK", "SPGI", "AXP"],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "CMG"],
    "Consumer Defensive": ["WMT", "PG", "COST", "KO", "PEP", "PM", "MDLZ", "MO", "CL", "KHC"],
    "Industrials": ["CAT", "UNP", "HON", "UPS", "BA", "RTX", "DE", "LMT", "GE", "MMM"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PXD", "VLO", "PSX", "OXY"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "XEL", "ED", "EXC", "WEC"],
    "Real Estate": ["PLD", "AMT", "EQIX", "CCI", "PSA", "O", "SPG", "WELL", "DLR", "AVB"],
    "Basic Materials": ["LIN", "APD", "SHW", "ECL", "FCX", "NEM", "NUE", "DOW", "DD", "PPG"],
    "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "TMUS", "CHTR", "EA"],
}


def _df_to_dict(df):
    if df is None or df.empty:
        return {}
    return df.fillna(0).to_dict()


def _extract_ohlcv(df, ticker=None):
    """Extract OHLCV from a DataFrame, handling MultiIndex columns."""
    if df is None or df.empty:
        return None
    # Handle MultiIndex columns from yf.download with multiple tickers
    if hasattr(df, "columns") and hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        if ticker and ticker in df.columns.get_level_values(1):
            df = df.xs(ticker, axis=1, level=1)
        else:
            # Flatten by taking first level
            df.columns = df.columns.get_level_values(0)
    return df


class YFinanceProvider(DataProvider):
    def _safe_yfinance_call(self, func, ticker, max_retries=3, retry_delay=2, *args, **kwargs):
        """Safely call yfinance methods with retry logic for rate limits"""
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                # Check if result is valid (not empty dict/list/None)
                if result is not None:
                    if isinstance(result, dict) and len(result) > 0:
                        return result
                    elif isinstance(result, list):
                        return result
                    elif not isinstance(result, dict):  # DataFrames, etc.
                        return result
                # If result is empty, wait and retry
                if attempt < max_retries - 1:
                    logger.warning(f"Empty result for {ticker}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
            except Exception as e:
                error_msg = str(e).lower()
                error_str = str(e)
                # Check for rate limit errors
                if "429" in error_str or "too many requests" in error_msg or "rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)  # Exponential backoff
                        logger.warning(f"Rate limit hit for {ticker}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded for {ticker} after {max_retries} attempts")
                        raise Exception(f"Yahoo Finance rate limit exceeded. Please try again in a few minutes.")
                elif "json" in error_msg.lower() or "decode" in error_msg.lower() or "expecting value" in error_msg:
                    # JSON decode error often means rate limit
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"JSON decode error for {ticker} (likely rate limit), waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to parse response for {ticker} after {max_retries} attempts")
                        raise Exception(f"Unable to fetch data for {ticker}. Yahoo Finance may be rate-limiting requests.")
                else:
                    # Other errors, re-raise immediately
                    logger.error(f"Error in yfinance call for {ticker}: {e}")
                    raise
        
        # If we get here, all retries failed
        logger.error(f"Failed yfinance call for {ticker} after {max_retries} attempts")
        return {}
    
    def _safe_get_info(self, ticker, max_retries=3, retry_delay=2):
        """Safely get ticker info with retry logic for rate limits"""
        def _get_info():
            ticker_obj = yf.Ticker(ticker)
            return ticker_obj.info or {}
        
        return self._safe_yfinance_call(_get_info, ticker, max_retries, retry_delay)
    
    def get_ticker_context(self, ticker):
        try:
            info = self._safe_get_info(ticker)
        except Exception as e:
            logger.error(f"Error getting ticker context for {ticker}: {e}")
            # Return minimal context on error
            return TickerContext(
                ticker=ticker,
                company_name=ticker,
                sector=None,
                industry=None,
                exchange=None,
                currency="USD",
                peers=[],
                benchmark=DEFAULT_BENCHMARK,
            )
        
        company_name = info.get("shortName") or info.get("longName") or ticker
        sector = info.get("sector")
        industry = info.get("industry")
        exchange = info.get("exchange")
        currency = info.get("currency") or "USD"
        peers = info.get("similarTickers") or []
        benchmark = SECTOR_ETF_MAP.get(sector, DEFAULT_BENCHMARK)
        return TickerContext(
            ticker=ticker,
            company_name=company_name,
            sector=sector,
            industry=industry,
            exchange=exchange,
            currency=currency,
            peers=peers,
            benchmark=benchmark,
        )

    def get_price_history(self, ticker, start, end, interval):
        history = None
        period = _period_from_range(start, end)

        # Method 1: Ticker.history with period (most reliable)
        try:
            t = yf.Ticker(ticker)
            history = t.history(period=period, interval=interval)
            history = _extract_ohlcv(history, ticker)
            if history is not None and not history.empty:
                logger.info(f"Got {len(history)} rows via Ticker.history(period={period})")
        except Exception as e:
            logger.warning(f"Ticker.history(period) failed: {e}")
            history = None

        # Method 2: Ticker.history with start/end
        if history is None or history.empty:
            try:
                t = yf.Ticker(ticker)
                history = t.history(start=start, end=end, interval=interval)
                history = _extract_ohlcv(history, ticker)
                if history is not None and not history.empty:
                    logger.info(f"Got {len(history)} rows via Ticker.history(start/end)")
            except Exception as e:
                logger.warning(f"Ticker.history(start/end) failed: {e}")
                history = None

        # Method 3: yf.download with period
        if history is None or history.empty:
            try:
                history = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
                history = _extract_ohlcv(history, ticker)
                if history is not None and not history.empty:
                    logger.info(f"Got {len(history)} rows via yf.download(period={period})")
            except Exception as e:
                logger.warning(f"yf.download(period) failed: {e}")
                history = None

        # Method 4: yf.download with start/end
        if history is None or history.empty:
            try:
                history = yf.download(ticker, start=start, end=end, interval=interval, progress=False, threads=False)
                history = _extract_ohlcv(history, ticker)
                if history is not None and not history.empty:
                    logger.info(f"Got {len(history)} rows via yf.download(start/end)")
            except Exception as e:
                logger.warning(f"yf.download(start/end) failed: {e}")
                history = None

        # Convert to PricePoint list
        points = []
        if history is None or history.empty:
            logger.error(f"All price fetch methods failed for {ticker}")
            return points

        for idx, row in history.iterrows():
            try:
                points.append(
                    PricePoint(
                        date=idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                        open=float(row.get("Open", 0) or 0),
                        high=float(row.get("High", 0) or 0),
                        low=float(row.get("Low", 0) or 0),
                        close=float(row.get("Close", 0) or 0),
                        volume=float(row.get("Volume", 0) or 0),
                    )
                )
            except Exception as e:
                logger.warning(f"Skipping row due to error: {e}")
                continue

        logger.info(f"Returning {len(points)} price points for {ticker}")
        return points

    def get_fundamentals(self, ticker):
        try:
            info = self._safe_get_info(ticker)
        except Exception as e:
            logger.error(f"Error getting fundamentals for {ticker}: {e}")
            info = {}
        
        # Calculate PEG ratio if we have the data
        pe = info.get("trailingPE")
        earnings_growth = info.get("earningsGrowth")
        peg_ratio = None
        if pe and earnings_growth and earnings_growth > 0:
            peg_ratio = pe / (earnings_growth * 100)
        
        return {
            # Valuation metrics
            "market_cap": info.get("marketCap"),
            "pe_ratio": pe,
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": peg_ratio,
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
            "ev_to_revenue": info.get("enterpriseToRevenue"),
            "enterprise_value": info.get("enterpriseValue"),
            "book_value": info.get("bookValue"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "target_mean_price": info.get("targetMeanPrice"),
            "target_high_price": info.get("targetHighPrice"),
            "target_low_price": info.get("targetLowPrice"),
            "number_of_analysts": info.get("numberOfAnalystOpinions"),
            "recommendation_mean": info.get("recommendationMean"),
            "recommendation_key": info.get("recommendationKey"),
            # Dividend metrics
            "dividend_yield": info.get("dividendYield"),
            "dividend_rate": info.get("dividendRate"),
            "payout_ratio": info.get("payoutRatio"),
            "ex_dividend_date": info.get("exDividendDate"),
            "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield"),
            # Profitability
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "gross_margins": info.get("grossMargins"),
            "operating_margins": info.get("operatingMargins"),
            "profit_margins": info.get("profitMargins"),
            # Balance sheet
            "beta": info.get("beta"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            "free_cash_flow": info.get("freeCashflow"),
            # Growth
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": earnings_growth,
            "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
            # Per share data
            "eps_trailing": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
            "revenue_per_share": info.get("revenuePerShare"),
            # 52-week data
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fifty_day_average": info.get("fiftyDayAverage"),
            "two_hundred_day_average": info.get("twoHundredDayAverage"),
        }

    def get_financial_statements(self, ticker):
        def _get_statements():
            yf_ticker = yf.Ticker(ticker)
            return {
                "income_statement": _df_to_dict(yf_ticker.financials),
                "balance_sheet": _df_to_dict(yf_ticker.balance_sheet),
                "cash_flow": _df_to_dict(yf_ticker.cashflow),
            }
        
        try:
            return self._safe_yfinance_call(_get_statements, ticker)
        except Exception as e:
            logger.error(f"Error getting financial statements for {ticker}: {e}")
            return {
                "income_statement": {},
                "balance_sheet": {},
                "cash_flow": {},
            }

    def get_news(self, ticker, start, end):
        """Fetch news from Finnhub (primary) with yfinance fallback."""
        items = []
        
        # Try Finnhub first (up to 100 articles)
        if FINNHUB_API_KEY:
            try:
                finnhub_items = self._fetch_finnhub_news(ticker, start, end)
                if finnhub_items:
                    logger.info(f"news: Got {len(finnhub_items)} articles from Finnhub for {ticker}")
                    return finnhub_items
            except Exception as e:
                logger.warning(f"news: Finnhub failed for {ticker}: {e}")
        
        # Fallback to yfinance
        logger.info(f"news: Using yfinance fallback for {ticker}")
        try:
            def _get_news():
                return yf.Ticker(ticker).news or []
            news = self._safe_yfinance_call(_get_news, ticker)
        except Exception as e:
            logger.error(f"Error getting news for {ticker}: {e}")
            news = []
        for item in news[:10]:
            content = item.get("content", item)
            title = content.get("title") or item.get("title") or "Untitled"
            
            provider = content.get("provider", {})
            publisher = provider.get("displayName") if isinstance(provider, dict) else item.get("publisher")
            
            canonical = content.get("canonicalUrl", {})
            url = canonical.get("url") if isinstance(canonical, dict) else item.get("link")
            if not url:
                click_through = content.get("clickThroughUrl", {})
                url = click_through.get("url") if isinstance(click_through, dict) else None
            
            published_at = content.get("pubDate") or item.get("providerPublishTime")
            if published_at and not isinstance(published_at, str):
                try:
                    published_at = datetime.utcfromtimestamp(published_at).isoformat()
                except (TypeError, ValueError):
                    published_at = None
            
            items.append(
                NewsItem(
                    title=title,
                    publisher=publisher,
                    url=url,
                    published_at=published_at,
                )
            )
        return items
    
    def _fetch_finnhub_news(self, ticker, start, end):
        """Fetch news from Finnhub API."""
        # Calculate date range (last 30 days or provided range)
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d") if isinstance(end, str) else datetime.utcnow()
            start_date = datetime.strptime(start, "%Y-%m-%d") if isinstance(start, str) else (end_date - timedelta(days=30))
        except (ValueError, TypeError):
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        
        params = {
            "symbol": ticker,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "token": FINNHUB_API_KEY,
        }
        
        response = requests.get(FINNHUB_NEWS_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            return []
        
        items = []
        for article in data[:100]:  # Limit to 100 articles
            published_at = article.get("datetime")
            if published_at:
                try:
                    published_at = datetime.utcfromtimestamp(published_at).isoformat()
                except (TypeError, ValueError):
                    published_at = None
            
            items.append(
                NewsItem(
                    title=article.get("headline") or "Untitled",
                    publisher=article.get("source"),
                    url=article.get("url"),
                    published_at=published_at,
                )
            )
        
        return items

    def get_social_posts(self, ticker, start, end):
        return []

    def get_peers(self, ticker):
        """Get peer tickers with multiple fallback strategies."""
        try:
            info = self._safe_get_info(ticker)
        except Exception as e:
            logger.error(f"Error getting peers for {ticker}: {e}")
            info = {}
        
        # Strategy 1: Use yfinance similarTickers
        peers = info.get("similarTickers") or []
        if isinstance(peers, list) and len(peers) >= 3:
            logger.info(f"peers: Found {len(peers)} peers via similarTickers for {ticker}")
            return [p for p in peers if p != ticker][:8]
        
        # Strategy 2: Use industry-based peers
        industry = info.get("industry")
        if industry and industry in INDUSTRY_PEERS:
            industry_peers = [p for p in INDUSTRY_PEERS[industry] if p != ticker]
            if industry_peers:
                logger.info(f"peers: Using {len(industry_peers)} industry peers for {ticker} ({industry})")
                return industry_peers[:8]
        
        # Strategy 3: Use sector leaders
        sector = info.get("sector")
        if sector and sector in SECTOR_LEADERS:
            sector_peers = [p for p in SECTOR_LEADERS[sector] if p != ticker]
            if sector_peers:
                logger.info(f"peers: Using {len(sector_peers)} sector leaders for {ticker} ({sector})")
                return sector_peers[:8]
        
        logger.warning(f"peers: No peers found for {ticker}")
        return []

    def get_sector_etf(self, ticker):
        try:
            info = self._safe_get_info(ticker)
        except Exception as e:
            logger.error(f"Error getting sector ETF for {ticker}: {e}")
            info = {}
        sector = info.get("sector")
        return SECTOR_ETF_MAP.get(sector, DEFAULT_BENCHMARK)

    def get_earnings(self, ticker):
        def _get_calendar():
            return yf.Ticker(ticker).calendar
        
        try:
            calendar = self._safe_yfinance_call(_get_calendar, ticker)
        except Exception as e:
            logger.error(f"Error getting earnings for {ticker}: {e}")
            calendar = None
        next_date = None
        if calendar:
            if hasattr(calendar, "empty"):
                if not calendar.empty and "Earnings Date" in calendar.index:
                    value = calendar.loc["Earnings Date"]
                    if hasattr(value, "iloc"):
                        next_date = value.iloc[0]
                    else:
                        next_date = value
            elif isinstance(calendar, dict):
                next_date = calendar.get("Earnings Date") or calendar.get("EarningsDate")
        
        # Unwrap from any container (list, tuple, ndarray, Series, etc.)
        # Keep unwrapping until we get a scalar
        for _ in range(5):  # Safety limit
            if next_date is None:
                break
            if isinstance(next_date, str):
                break
            # Check if it's iterable/indexable and not a date object
            if hasattr(next_date, "__iter__") and hasattr(next_date, "__getitem__"):
                try:
                    inner = next_date[0] if len(next_date) > 0 else None
                    next_date = inner
                except (TypeError, IndexError, KeyError):
                    break
            else:
                break
        
        # Convert to clean date string
        if next_date is not None:
            date_str = _format_date(next_date)
            next_date = date_str
        
        return {
            "next_earnings_date": next_date,
            "surprise_history": [],
        }


def _format_date(value):
    """Convert various date types to YYYY-MM-DD string."""
    if value is None:
        return None
    if isinstance(value, str):
        # Already a string, clean it up
        if "T" in value:
            return value.split("T")[0]
        return value
    # Try pandas Timestamp
    try:
        return value.to_pydatetime().date().isoformat()
    except AttributeError:
        pass
    # Try datetime.date or datetime.datetime
    try:
        if hasattr(value, "isoformat"):
            result = value.isoformat()
            if "T" in result:
                return result.split("T")[0]
            return result
    except Exception:
        pass
    # Last resort
    return str(value)


def _period_from_range(start, end):
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        days = max(1, (end_dt - start_dt).days)
    except (TypeError, ValueError):
        return "1y"
    if days >= 365 * 5:
        return "5y"
    if days >= 365:
        return "1y"
    if days >= 180:
        return "6mo"
    if days >= 90:
        return "3mo"
    if days >= 30:
        return "1mo"
    if days >= 7:
        return "5d"
    return "5d"
