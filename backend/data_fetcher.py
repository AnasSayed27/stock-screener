"""
Data fetcher — retrieves stock lists from nselib and financial data from yfinance.

Features:
- Nifty 500 stock list (with hardcoded fallback)
- Normalised financial data dict from yfinance
- JSON file caching with configurable TTL
- 1-second inter-request delay
- Graceful handling of all None / missing values
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

from config import CACHE_DIR, CACHE_TTL_HOURS

logger = logging.getLogger(__name__)

# Track the last request time for rate-limiting
_last_request_time: float = 0.0


# ---------------------------------------------------------------------------
# Hardcoded fallback stock list (top ~50 Nifty 50 + popular largecaps)
# ---------------------------------------------------------------------------
FALLBACK_STOCKS: list[dict[str, str]] = [
    {"symbol": "RELIANCE", "name": "Reliance Industries"},
    {"symbol": "TCS", "name": "Tata Consultancy Services"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank"},
    {"symbol": "INFY", "name": "Infosys"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever"},
    {"symbol": "SBIN", "name": "State Bank of India"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel"},
    {"symbol": "ITC", "name": "ITC"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank"},
    {"symbol": "LT", "name": "Larsen & Toubro"},
    {"symbol": "AXISBANK", "name": "Axis Bank"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki"},
    {"symbol": "TITAN", "name": "Titan Company"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharma"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement"},
    {"symbol": "NESTLEIND", "name": "Nestle India"},
    {"symbol": "WIPRO", "name": "Wipro"},
    {"symbol": "HCLTECH", "name": "HCL Technologies"},
    {"symbol": "POWERGRID", "name": "Power Grid Corp"},
    {"symbol": "NTPC", "name": "NTPC"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors"},
    {"symbol": "TATASTEEL", "name": "Tata Steel"},
    {"symbol": "ONGC", "name": "Oil and Natural Gas Corp"},
    {"symbol": "COALINDIA", "name": "Coal India"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv"},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories"},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories"},
    {"symbol": "CIPLA", "name": "Cipla"},
    {"symbol": "EICHERMOT", "name": "Eicher Motors"},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp"},
    {"symbol": "TECHM", "name": "Tech Mahindra"},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance"},
    {"symbol": "BRITANNIA", "name": "Britannia Industries"},
    {"symbol": "GRASIM", "name": "Grasim Industries"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank"},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel"},
    {"symbol": "M&M", "name": "Mahindra & Mahindra"},
    {"symbol": "PIDILITIND", "name": "Pidilite Industries"},
    {"symbol": "DABUR", "name": "Dabur India"},
    {"symbol": "GODREJCP", "name": "Godrej Consumer Products"},
    {"symbol": "HAVELLS", "name": "Havells India"},
    {"symbol": "BERGEPAINT", "name": "Berger Paints"},
]


# ---------------------------------------------------------------------------
# Nifty 500 stock list
# ---------------------------------------------------------------------------

def _fetch_from_nselib(func_name: str, fallback_label: str) -> list[dict[str, str]]:
    """Generic helper to fetch index constituents from nselib."""
    try:
        from nselib import capital_market
        func = getattr(capital_market, func_name)
        df = func()
        if df is not None and not df.empty:
            stocks = []
            sym_col = _find_column(df, ["Symbol", "symbol", "SYMBOL"])
            name_col = _find_column(df, ["Company Name", "company name", "COMPANY NAME",
                                          "Company", "Name Of Company"])
            if sym_col:
                for _, row in df.iterrows():
                    symbol = str(row[sym_col]).strip()
                    name = str(row[name_col]).strip() if name_col else symbol
                    if symbol:
                        stocks.append({"symbol": symbol, "name": name})
            if stocks:
                logger.info("Fetched %d stocks from nselib (%s)", len(stocks), func_name)
                return stocks
    except Exception as exc:
        logger.warning("nselib %s failed, using fallback list: %s", func_name, exc)

    logger.info("Using fallback stock list (%d stocks) for %s", len(FALLBACK_STOCKS), fallback_label)
    return list(FALLBACK_STOCKS)

def get_nifty500_stocks() -> list[dict[str, str]]:
    return _fetch_from_nselib('nifty500_equity_list', 'Nifty 500')

def get_nifty50_stocks() -> list[dict[str, str]]:
    return _fetch_from_nselib('nifty50_equity_list', 'Nifty 50')

def get_niftymidcap150_stocks() -> list[dict[str, str]]:
    return _fetch_from_nselib('niftymidcap150_equity_list', 'Nifty Midcap 150')

def get_niftynext50_stocks() -> list[dict[str, str]]:
    return _fetch_from_nselib('niftynext50_equity_list', 'Nifty Next 50')

def get_niftysmallcap250_stocks() -> list[dict[str, str]]:
    return _fetch_from_nselib('niftysmallcap250_equity_list', 'Nifty Smallcap 250')

def get_fno_stocks() -> list[dict[str, str]]:
    return _fetch_from_nselib('fno_equity_list', 'F&O Stocks')


def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first column name from *candidates* that exists in *df*."""
    for c in candidates:
        if c in df.columns:
            return c
    # Case-insensitive fallback
    lower_map = {col.lower(): col for col in df.columns}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_path(ticker: str) -> str:
    safe = ticker.replace(".", "_").replace("/", "_").upper()
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _read_cache(ticker: str) -> Optional[dict]:
    """Return cached data if fresh, else None."""
    path = _cache_path(ticker)
    if not os.path.isfile(path):
        return None
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        if datetime.now() - mtime > timedelta(hours=CACHE_TTL_HOURS):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.debug("Cache read failed for %s: %s", ticker, exc)
        return None


def _write_cache(ticker: str, data: dict) -> None:
    """Persist *data* to the cache file."""
    path = _cache_path(ticker)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
    except Exception as exc:
        logger.debug("Cache write failed for %s: %s", ticker, exc)


# ---------------------------------------------------------------------------
# Rate-limiter
# ---------------------------------------------------------------------------

def _rate_limit() -> None:
    """Ensure at least 1 second between yfinance requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_request_time = time.time()


# ---------------------------------------------------------------------------
# yfinance data normalisation helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any) -> Optional[float]:
    """Convert *val* to float, returning None on failure."""
    if val is None:
        return None
    try:
        f = float(val)
        if pd.isna(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _normalise_info(info: dict) -> dict:
    """Extract and sanitise relevant fields from the yfinance info dict."""
    keys = [
        "shortName", "longName", "sector", "industry",
        "marketCap", "enterpriseValue",
        "trailingPE", "forwardPE", "priceToBook",
        "returnOnEquity", "debtToEquity", "currentRatio",
        "trailingEps", "bookValue",
        "operatingMargins", "profitMargins", "grossMargins",
        "operatingCashflow", "freeCashflow",
        "sharesOutstanding",
        "earningsGrowth", "revenueGrowth",
        "currentPrice", "regularMarketPrice",
        "totalRevenue", "totalDebt", "totalCash",
        "ebitda", "totalAssets",
    ]
    out: dict[str, Any] = {}
    for k in keys:
        out[k] = info.get(k)
    return out


def _normalise_stmt(df: Optional[pd.DataFrame], field_map: dict[str, list[str]]) -> dict[str, dict]:
    """
    Convert a yfinance statement DataFrame (columns = dates, rows = items)
    into ``{year_str: {field: value, ...}, ...}``.

    *field_map* maps our canonical field names to a list of possible row labels.
    """
    result: dict[str, dict] = {}
    if df is None or df.empty:
        return result

    for col in df.columns:
        year_str = str(col)[:10]  # e.g. "2024-03-31"
        year_data: dict[str, Optional[float]] = {}
        for field, candidates in field_map.items():
            val = None
            for c in candidates:
                if c in df.index:
                    val = _safe_float(df.loc[c, col])
                    if val is not None:
                        break
            year_data[field] = val
        result[year_str] = year_data

    return result


# ---------------------------------------------------------------------------
# Main data-fetching function
# ---------------------------------------------------------------------------

def get_stock_data(ticker: str) -> Optional[dict[str, Any]]:
    """
    Fetch and normalise all financial data for *ticker* from yfinance.

    Returns a dict with keys: ``info``, ``income_stmt``, ``balance_sheet``,
    ``cashflow``.  Returns None if fetching fails entirely.
    """
    # Ensure .NS suffix for NSE stocks
    yf_ticker = ticker.strip()
    if not yf_ticker.endswith(".NS") and not yf_ticker.endswith(".BO"):
        yf_ticker = yf_ticker + ".NS"

    # Check cache first
    cached = _read_cache(yf_ticker)
    if cached is not None:
        logger.debug("Cache hit for %s", yf_ticker)
        return cached

    logger.info("Fetching data for %s from yfinance …", yf_ticker)
    _rate_limit()

    try:
        import yfinance as yf
        stock = yf.Ticker(yf_ticker)

        # --- info ---
        try:
            raw_info = stock.info or {}
        except Exception:
            raw_info = {}
        info = _normalise_info(raw_info)

        # --- income statement ---
        income_map = {
            "revenue": ["Total Revenue", "Revenue", "TotalRevenue"],
            "net_income": ["Net Income", "NetIncome", "Net Income Common Stockholders",
                           "Net Income From Continuing Operation Net Minority Interest"],
            "ebit": ["EBIT", "Ebit", "Operating Income"],
            "operating_income": ["Operating Income", "OperatingIncome", "EBIT"],
            "gross_profit": ["Gross Profit", "GrossProfit"],
            "interest_expense": ["Interest Expense", "InterestExpense"],
            "tax_provision": ["Tax Provision", "TaxProvision", "Income Tax Expense"],
        }
        try:
            inc_df = stock.income_stmt
        except Exception:
            inc_df = None
        income_stmt = _normalise_stmt(inc_df, income_map)

        # --- balance sheet ---
        bs_map = {
            "total_assets": ["Total Assets", "TotalAssets"],
            "total_debt": ["Total Debt", "TotalDebt", "Long Term Debt", "LongTermDebt"],
            "long_term_debt": ["Long Term Debt", "LongTermDebt", "Long Term Debt And Capital Lease Obligation"],
            "total_equity": ["Total Equity Gross Minority Interest",
                             "Stockholders Equity", "StockholdersEquity",
                             "Total Stockholder Equity", "Common Stock Equity"],
            "current_assets": ["Current Assets", "CurrentAssets", "Total Current Assets"],
            "current_liabilities": ["Current Liabilities", "CurrentLiabilities",
                                     "Total Current Liabilities",
                                     "Current Debt And Capital Lease Obligation"],
            "cash": ["Cash And Cash Equivalents", "Cash", "CashAndCashEquivalents",
                      "Cash Cash Equivalents And Short Term Investments"],
            "shares_outstanding": ["Share Issued", "ShareIssued", "Ordinary Shares Number"],
        }
        try:
            bs_df = stock.balance_sheet
        except Exception:
            bs_df = None
        balance_sheet = _normalise_stmt(bs_df, bs_map)

        # --- cash-flow statement ---
        cf_map = {
            "operating_cf": ["Operating Cash Flow", "OperatingCashFlow",
                              "Cash Flow From Continuing Operating Activities",
                              "Total Cash From Operating Activities"],
            "capex": ["Capital Expenditure", "CapitalExpenditure",
                       "Purchase Of PPE", "Capital Expenditures"],
            "fcf": ["Free Cash Flow", "FreeCashFlow"],
        }
        try:
            cf_df = stock.cashflow
        except Exception:
            cf_df = None
        cashflow = _normalise_stmt(cf_df, cf_map)

        # Compute FCF if missing (operating_cf + capex, capex is usually negative)
        for yr, yr_data in cashflow.items():
            if yr_data.get("fcf") is None:
                op_cf = yr_data.get("operating_cf")
                capex = yr_data.get("capex")
                if op_cf is not None and capex is not None:
                    # capex from yfinance is typically negative
                    yr_data["fcf"] = op_cf + capex if capex < 0 else op_cf - abs(capex)

        data = {
            "info": info,
            "income_stmt": income_stmt,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
        }

        _write_cache(yf_ticker, data)
        return data

    except Exception as exc:
        logger.error("Failed to fetch data for %s: %s", yf_ticker, exc)
        return None
