import datetime
import os
import pandas as pd
import requests
import time
import yfinance as yf
from typing import Optional, List, Dict, Any
import json

from src.data.cache import get_cache
from src.data.models import (
    CompanyNews,
    FinancialMetrics,
    Price,
    LineItem,
    InsiderTrade
)

# Global cache instance
_cache = get_cache()

# Alpaca API configuration
ALPACA_BASE_URL = "https://data.alpaca.markets/v2"
ALPACA_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"

def _make_api_request(url: str, headers: dict, method: str = "GET", json_data: dict = None, max_retries: int = 3) -> requests.Response:
    """
    Make an API request with rate limiting handling and moderate backoff.
    
    Args:
        url: The URL to request
        headers: Headers to include in the request
        method: HTTP method (GET or POST)
        json_data: JSON data for POST requests
        max_retries: Maximum number of retries (default: 3)
    
    Returns:
        requests.Response: The response object
    
    Raises:
        Exception: If the request fails with a non-429 error
    """
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        else:
            response = requests.get(url, headers=headers)
        
        if response.status_code == 429 and attempt < max_retries:
            # Linear backoff: 60s, 90s, 120s, 150s...
            delay = 60 + (30 * attempt)
            print(f"Rate limited (429). Attempt {attempt + 1}/{max_retries + 1}. Waiting {delay}s before retrying...")
            time.sleep(delay)
            continue
        
        # Return the response (whether success, other errors, or final 429)
        return response

def _get_alpaca_headers() -> dict:
    """Get Alpaca API headers."""
    headers = {}
    api_key = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_API_SECRET")
    
    if api_key and secret_key:
        headers["APCA-API-KEY-ID"] = api_key
        headers["APCA-API-SECRET-KEY"] = secret_key
    
    return headers

def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data from cache or multiple free sources."""
    cache_key = f"{ticker}_{start_date}_{end_date}"
    
    # Check cache first
    if cached_data := _cache.get_prices(cache_key):
        return [Price(**price) for price in cached_data]

    # Try Alpaca first (free tier available)
    try:
        prices = _get_prices_alpaca(ticker, start_date, end_date)
        if prices:
            _cache.set_prices(cache_key, [p.model_dump() for p in prices])
            return prices
    except Exception as e:
        print(f"Alpaca API failed: {e}")

    # Fallback to yfinance
    try:
        prices = _get_prices_yfinance(ticker, start_date, end_date)
        if prices:
            _cache.set_prices(cache_key, [p.model_dump() for p in prices])
            return prices
    except Exception as e:
        print(f"yfinance failed: {e}")
    
    # Fallback to Alpha Vantage (free tier)
    try:
        prices = _get_prices_alpha_vantage(ticker, start_date, end_date)
        if prices:
            _cache.set_prices(cache_key, [p.model_dump() for p in prices])
            return prices
    except Exception as e:
        print(f"Alpha Vantage failed: {e}")

    return []

def _get_prices_alpaca(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch prices from Alpaca API."""
    headers = _get_alpaca_headers()
    
    url = f"{ALPACA_BASE_URL}/stocks/{ticker}/bars"
    params = {
        "start": start_date,
        "end": end_date,
        "timeframe": "1Day",
        "adjustment": "raw",
        "feed": "iex",  # Use IEX feed for free tier
        "sort": "asc"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Alpaca API error: {response.status_code} - {response.text}")
    
    data = response.json()
    prices = []
    
    for bar in data.get("bars", []):
        price = Price(
            time=bar["t"],
            open=float(bar["o"]),
            high=float(bar["h"]),
            low=float(bar["l"]),
            close=float(bar["c"]),
            volume=int(bar["v"])
        )
        prices.append(price)
    
    return prices

def _get_prices_yfinance(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch prices from yfinance (Yahoo Finance)."""
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    
    prices = []
    for date, row in df.iterrows():
        price = Price(
            time=date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"])
        )
        prices.append(price)
    
    return prices

def _get_prices_alpha_vantage(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch prices from Alpha Vantage API."""
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise Exception("Alpha Vantage API key not found")
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "apikey": api_key,
        "outputsize": "full"
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Alpha Vantage API error: {response.status_code}")
    
    data = response.json()
    time_series = data.get("Time Series (Daily)", {})
    
    prices = []
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    for date_str, values in time_series.items():
        date_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        if start_dt <= date_dt <= end_dt:
            price = Price(
                time=f"{date_str}T00:00:00Z",
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=int(values["5. volume"])
            )
            prices.append(price)
    
    # Sort by date
    prices.sort(key=lambda x: x.time)
    return prices

def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics using yfinance."""
    cache_key = f"{ticker}_{period}_{end_date}_{limit}"
    
    if cached_data := _cache.get_financial_metrics(cache_key):
        return [FinancialMetrics(**metric) for metric in cached_data]

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        metrics = []
        
        # Get the most recent data
        latest_financials = financials.iloc[:, 0] if not financials.empty else {}
        latest_balance = balance_sheet.iloc[:, 0] if not balance_sheet.empty else {}
        latest_cashflow = cashflow.iloc[:, 0] if not cashflow.empty else {}
        
        # Calculate derived metrics
        total_debt = latest_balance.get('Total Debt', 0) or 0
        shareholders_equity = latest_balance.get('Stockholders Equity', 0) or 0
        total_assets = latest_balance.get('Total Assets', 0) or 0
        current_assets = latest_balance.get('Current Assets', 0) or 0
        current_liabilities = latest_balance.get('Current Liabilities', 0) or 0
        total_revenue = latest_financials.get('Total Revenue', 0) or 0
        net_income = latest_financials.get('Net Income', 0) or 0
        gross_profit = latest_financials.get('Gross Profit', 0) or 0
        operating_income = latest_financials.get('Operating Income', 0) or 0
        free_cash_flow = latest_cashflow.get('Free Cash Flow', 0) or 0
        
        # Calculate ratios
        debt_to_equity = (total_debt / shareholders_equity) if shareholders_equity != 0 else None
        current_ratio = (current_assets / current_liabilities) if current_liabilities != 0 else None
        gross_margin = (gross_profit / total_revenue) if total_revenue != 0 else None
        operating_margin = (operating_income / total_revenue) if total_revenue != 0 else None
        net_margin = (net_income / total_revenue) if total_revenue != 0 else None
        return_on_equity = (net_income / shareholders_equity) if shareholders_equity != 0 else None
        return_on_assets = (net_income / total_assets) if total_assets != 0 else None
        
        metric = FinancialMetrics(
            ticker=ticker,
            report_period=end_date,
            period=period,
            currency=info.get('currency', 'USD'),
            market_cap=info.get('marketCap'),
            enterprise_value=info.get('enterpriseValue'),
            price_to_earnings_ratio=info.get('trailingPE'),
            price_to_book_ratio=info.get('priceToBook'),
            price_to_sales_ratio=info.get('priceToSalesTrailing12Months'),
            enterprise_value_to_ebitda_ratio=info.get('enterpriseToEbitda'),
            enterprise_value_to_revenue_ratio=info.get('enterpriseToRevenue'),
            free_cash_flow_yield=None,  # Calculate if needed
            peg_ratio=info.get('pegRatio'),
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            return_on_equity=return_on_equity or info.get('returnOnEquity'),
            return_on_assets=return_on_assets or info.get('returnOnAssets'),
            return_on_invested_capital=None,  # Not directly available
            asset_turnover=None,  # Calculate if needed
            inventory_turnover=None,  # Calculate if needed
            receivables_turnover=None,  # Calculate if needed
            days_sales_outstanding=None,  # Calculate if needed
            operating_cycle=None,  # Calculate if needed
            working_capital_turnover=None,  # Calculate if needed
            current_ratio=current_ratio,
            quick_ratio=info.get('quickRatio'),
            cash_ratio=None,  # Calculate if needed
            operating_cash_flow_ratio=None,  # Calculate if needed
            debt_to_equity=debt_to_equity,
            debt_to_assets=(total_debt / total_assets) if total_assets != 0 else None,
            interest_coverage=None,  # Calculate if needed
            revenue_growth=info.get('revenueGrowth'),
            earnings_growth=info.get('earningsGrowth'),
            book_value_growth=None,  # Calculate if needed
            earnings_per_share_growth=None,  # Calculate if needed
            free_cash_flow_growth=None,  # Calculate if needed
            operating_income_growth=None,  # Calculate if needed
            ebitda_growth=None,  # Calculate if needed
            payout_ratio=info.get('payoutRatio'),
            earnings_per_share=info.get('trailingEps'),
            book_value_per_share=info.get('bookValue'),
            free_cash_flow_per_share=None  # Calculate if needed
        )
        metrics.append(metric)
        
        _cache.set_financial_metrics(cache_key, [m.model_dump() for m in metrics])
        return metrics
        
    except Exception as e:
        print(f"Error fetching financial metrics: {e}")
        return []

def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """Search for specific line items using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        results = []
        
        # Combine all financial statements
        all_data = {}
        if not financials.empty:
            all_data.update(financials.to_dict())
        if not balance_sheet.empty:
            all_data.update(balance_sheet.to_dict())
        if not cashflow.empty:
            all_data.update(cashflow.to_dict())
        
        # Search for requested line items
        for line_item in line_items:
            for key, values in all_data.items():
                if line_item.lower() in key.lower():
                    if values and len(values) > 0:
                        latest_value = list(values.values())[0]
                        # Create LineItem with base fields and add the specific line item as extra field
                        result_data = {
                            "ticker": ticker,
                            "report_period": end_date,
                            "period": period,
                            "currency": info.get('currency', 'USD'),
                            key.replace(" ", "_").lower(): float(latest_value) if latest_value else 0
                        }
                        result = LineItem(**result_data)
                        results.append(result)
                        break
        
        return results[:limit]
        
    except Exception as e:
        print(f"Error searching line items: {e}")
        return []

def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[InsiderTrade]:
    """Fetch insider trades - Note: Limited free sources available."""
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"
    
    if cached_data := _cache.get_insider_trades(cache_key):
        return [InsiderTrade(**trade) for trade in cached_data]

    # Try SEC EDGAR API (free but limited)
    try:
        trades = _get_insider_trades_sec(ticker, start_date, end_date, limit)
        if trades:
            _cache.set_insider_trades(cache_key, [trade.model_dump() for trade in trades])
            return trades
    except Exception as e:
        print(f"SEC EDGAR API failed: {e}")
    
    return []

def _get_insider_trades_sec(ticker: str, start_date: str, end_date: str, limit: int) -> list[InsiderTrade]:
    """Fetch insider trades from SEC EDGAR (limited functionality)."""
    # Note: SEC EDGAR API has limitations and may require additional processing
    # This is a simplified implementation
    print("Note: Insider trading data requires premium APIs or web scraping from SEC EDGAR")
    return []

def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[CompanyNews]:
    """Fetch company news from free sources."""
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"
    
    if cached_data := _cache.get_company_news(cache_key):
        return [CompanyNews(**news) for news in cached_data]

    # Try Alpaca News API first
    try:
        news = _get_news_alpaca(ticker, start_date, end_date, limit)
        if news:
            _cache.set_company_news(cache_key, [n.model_dump() for n in news])
            return news
    except Exception as e:
        print(f"Alpaca News API failed: {e}")
    
    # Fallback to NewsAPI (free tier)
    try:
        news = _get_news_newsapi(ticker, start_date, end_date, limit)
        if news:
            _cache.set_company_news(cache_key, [n.model_dump() for n in news])
            return news
    except Exception as e:
        print(f"NewsAPI failed: {e}")
    
    return []

def _get_news_alpaca(ticker: str, start_date: str, end_date: str, limit: int) -> list[CompanyNews]:
    """Fetch news from Alpaca News API."""
    headers = _get_alpaca_headers()
    
    params = {
        "symbols": ticker,
        "start": start_date + "T00:00:00Z" if start_date else None,
        "end": end_date + "T23:59:59Z",
        "sort": "desc",
        "page_size": min(limit, 50)  # Alpaca limit
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    response = requests.get(ALPACA_NEWS_URL, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Alpaca News API error: {response.status_code}")
    
    data = response.json()
    news_items = []
    
    for article in data.get("news", []):
        news_item = CompanyNews(
            ticker=ticker,
            title=article["headline"],
            author=article.get("author", "Unknown"),
            source=article.get("source", "Alpaca"),
            date=article["created_at"],
            url=article.get("url", ""),
            sentiment=None  # Alpaca may provide sentiment in some cases
        )
        news_items.append(news_item)
    
    return news_items

def _get_news_newsapi(ticker: str, start_date: str, end_date: str, limit: int) -> list[CompanyNews]:
    """Fetch news from NewsAPI."""
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise Exception("NewsAPI key not found")
    
    # Get company name for better search results
    try:
        stock = yf.Ticker(ticker)
        company_name = stock.info.get('longName', ticker)
    except:
        company_name = ticker
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f"{ticker} OR {company_name}",
        "from": start_date,
        "to": end_date,
        "sortBy": "publishedAt",
        "pageSize": min(limit, 100),  # NewsAPI limit
        "apiKey": api_key
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"NewsAPI error: {response.status_code}")
    
    data = response.json()
    news_items = []
    
    for article in data.get("articles", []):
        news_item = CompanyNews(
            ticker=ticker,
            title=article["title"],
            author=article.get("author", "Unknown"),
            source=article.get("source", {}).get("name", "NewsAPI"),
            date=article["publishedAt"],
            url=article.get("url", ""),
            sentiment=None  # NewsAPI doesn't provide sentiment
        )
        news_items.append(news_item)
    
    return news_items

def get_market_cap(ticker: str, end_date: str) -> float | None:
    """Fetch market cap using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get('marketCap')
    except Exception as e:
        print(f"Error fetching market cap: {e}")
        return None

def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df

def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get price data and convert to DataFrame."""
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)
