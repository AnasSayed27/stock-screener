r"""
FastAPI application — entry point for the stock screener backend.

Run with:
    cd stock-screener
    .\\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import sys

# Ensure the backend directory is on sys.path so sibling modules
# (analyzer, screener, etc.) can be imported regardless of cwd.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from analyzer import analyze_stock, screen_stock
from data_fetcher import get_nifty50_stocks, get_nifty500_stocks, get_niftymidcap150_stocks, get_niftynext50_stocks, get_niftysmallcap250_stocks, get_fno_stocks
from models import (
    PostmortemCreate,
    PostmortemResponse,
    ScreenRequest,
    ScreenResult,
    StockAnalysis,
    ThesisCreate,
    ThesisResponse,
)
from thesis import (
    delete_thesis,
    get_all_postmortems,
    get_all_theses,
    get_thesis,
    save_postmortem,
    save_thesis,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Stock Screener API",
    description="Backend for the NSE stock screening and analysis tool",
    version="0.1.0",
)

# CORS — allow everything on localhost for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Static files & SPA fallback
# ---------------------------------------------------------------------------
import os

_FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend",
)

if os.path.isdir(_FRONTEND_DIR):
    _CSS_DIR = os.path.join(_FRONTEND_DIR, "css")
    _JS_DIR = os.path.join(_FRONTEND_DIR, "js")
    _ASSETS_DIR = os.path.join(_FRONTEND_DIR, "assets")
    if os.path.isdir(_CSS_DIR):
        app.mount("/css", StaticFiles(directory=_CSS_DIR), name="css")
    if os.path.isdir(_JS_DIR):
        app.mount("/js", StaticFiles(directory=_JS_DIR), name="js")
    if os.path.isdir(_ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the frontend index.html."""
    index = os.path.join(_FRONTEND_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse(
        {"message": "Stock Screener API is running. Frontend not found."},
        status_code=200,
    )


# ---------------------------------------------------------------------------
# Stock list
# ---------------------------------------------------------------------------

@app.get("/api/stocks", response_model=list[dict])
async def api_get_stocks():
    """Return the stock universe (Nifty 500 or fallback)."""
    try:
        stocks = get_nifty500_stocks()
        return stocks
    except Exception as exc:
        logger.error("Failed to get stock list: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Screening
# ---------------------------------------------------------------------------

@app.post("/api/screen", response_model=list[ScreenResult])
async def api_screen(request: Optional[ScreenRequest] = None):
    """
    Screen stocks and return quality-sorted results.

    If ``tickers`` is empty the full stock universe is scanned (slow!).
    Otherwise only the provided tickers are analysed.
    """
    tickers = request.tickers if request else []
    if not tickers:
        universe = request.universe if request else "nifty500"
        if universe == "nifty50":
            stocks = get_nifty50_stocks()
        elif universe == "nifty500":
            stocks = get_nifty500_stocks()
        elif universe == "niftymidcap150":
            stocks = get_niftymidcap150_stocks()
        elif universe == "niftynext50":
            stocks = get_niftynext50_stocks()
        elif universe == "niftysmallcap250":
            stocks = get_niftysmallcap250_stocks()
        elif universe == "fno":
            stocks = get_fno_stocks()
        else:
            stocks = get_nifty500_stocks()
        tickers = [s["symbol"] for s in stocks]

    results: list[ScreenResult] = []
    total = len(tickers)
    for idx, ticker in enumerate(tickers, 1):
        logger.info("Screening %d/%d: %s", idx, total, ticker)
        try:
            result = screen_stock(ticker)
            if result is not None:
                results.append(result)
        except Exception as exc:
            logger.warning("Screening failed for %s: %s", ticker, exc)

    # Sort by quality score descending
    results.sort(key=lambda r: r.quality_pct, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Single stock analysis
# ---------------------------------------------------------------------------

@app.get("/api/stock/{ticker}", response_model=StockAnalysis)
async def api_analyze_stock(ticker: str):
    """Full analysis for a single stock."""
    try:
        analysis = analyze_stock(ticker)
        if analysis is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch data for {ticker}",
            )
        return analysis
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Analysis failed for %s: %s", ticker, exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Theses
# ---------------------------------------------------------------------------

@app.get("/api/theses", response_model=list[ThesisResponse])
async def api_list_theses():
    """List all saved investment theses."""
    return get_all_theses()


@app.get("/api/theses/{ticker}", response_model=Optional[ThesisResponse])
@app.get("/api/thesis/{ticker}", response_model=Optional[ThesisResponse])
async def api_get_thesis(ticker: str):
    """Get a specific thesis."""
    thesis = get_thesis(ticker)
    if thesis is None:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return thesis


@app.post("/api/theses", response_model=ThesisResponse)
@app.post("/api/thesis", response_model=ThesisResponse)
async def api_create_thesis(thesis: ThesisCreate):
    """Create or update an investment thesis."""
    return save_thesis(thesis)


@app.delete("/api/theses/{ticker}")
@app.delete("/api/thesis/{ticker}")
async def api_delete_thesis(ticker: str):
    """Delete an investment thesis."""
    deleted = delete_thesis(ticker)
    if not deleted:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return {"message": f"Thesis for {ticker} deleted"}


# ---------------------------------------------------------------------------
# Postmortems
# ---------------------------------------------------------------------------

@app.get("/api/postmortems", response_model=list[PostmortemResponse])
async def api_list_postmortems():
    """List all postmortems."""
    return get_all_postmortems()


@app.post("/api/postmortems", response_model=PostmortemResponse)
@app.post("/api/postmortem", response_model=PostmortemResponse)
async def api_create_postmortem(postmortem: PostmortemCreate):
    """Create a postmortem."""
    return save_postmortem(postmortem)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    """Simple health-check endpoint."""
    return {"status": "ok", "message": "Stock Screener API is running"}
