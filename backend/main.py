r"""
FastAPI application — entry point for the stock screener backend.

Run with:
    cd stock-screener
    .\\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import sys
import shutil
import json
from dotenv import load_dotenv
load_dotenv()


# Ensure the backend directory is on sys.path so sibling modules
# (analyzer, screener, etc.) can be imported regardless of cwd.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


import logging
from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from analyzer import analyze_stock, screen_stock
from data_fetcher import get_nifty50_stocks, get_nifty500_stocks, get_niftymidcap150_stocks, get_niftynext50_stocks, get_niftysmallcap250_stocks, get_fno_stocks
from security_utils import safe_join, sanitize_ticker, validate_uuid
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
    delete_postmortem,
    delete_thesis,
    get_all_postmortems,
    get_all_theses,
    get_postmortem,
    get_thesis,
    save_postmortem,
    save_thesis,
    update_postmortem,
)
from config import AI_ENABLED, AI_MODEL, AI_TEMP_DIR
from ai_research import upload_documents, analyze_documents, get_saved_reports, clear_session
from usage_tracker import get_current_usage

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

# CORS — restricted to localhost origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Graceful shutdown & terminal Ctrl+C signal handling
# ---------------------------------------------------------------------------
import signal

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown initiated. Terminating active background processes...")
    try:
        from discovery import cancel_discovery
        cancel_discovery()
    except Exception as e:
        logger.warning("Error during shutdown cancellation: %s", e)

def _handle_terminal_exit_signal(sig, frame):
    logger.info("Received terminal signal %s (Ctrl+C). Force stopping active processes...", sig)
    try:
        from discovery import cancel_discovery
        cancel_discovery()
    except Exception:
        pass
    os._exit(0)

try:
    signal.signal(signal.SIGINT, _handle_terminal_exit_signal)
    signal.signal(signal.SIGTERM, _handle_terminal_exit_signal)
except Exception as _sig_err:
    logger.warning("Could not register terminal signal handler: %s", _sig_err)



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
async def api_screen(req: Request, request: Optional[ScreenRequest] = None):
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
        if await req.is_disconnected():
            logger.info("Client disconnected. Aborting screening at %d/%d (%s)", idx, total, ticker)
            break
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


@app.get("/api/postmortems/{postmortem_id}", response_model=PostmortemResponse)
@app.get("/api/postmortem/{postmortem_id}", response_model=PostmortemResponse)
async def api_get_postmortem(postmortem_id: str):
    """Get a single postmortem by ID."""
    pm = get_postmortem(postmortem_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Postmortem not found")
    return pm


@app.put("/api/postmortems/{postmortem_id}", response_model=PostmortemResponse)
@app.put("/api/postmortem/{postmortem_id}", response_model=PostmortemResponse)
async def api_update_postmortem(postmortem_id: str, postmortem: PostmortemCreate):
    """Update an existing postmortem by ID."""
    pm = update_postmortem(postmortem_id, postmortem)
    if not pm:
        raise HTTPException(status_code=404, detail="Postmortem not found")
    return pm


@app.delete("/api/postmortems/{postmortem_id}")
@app.delete("/api/postmortem/{postmortem_id}")
async def api_delete_postmortem(postmortem_id: str):
    """Delete a postmortem by ID."""
    deleted = delete_postmortem(postmortem_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Postmortem not found or delete failed")
    return {"message": "Postmortem deleted"}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    """Simple health-check endpoint."""
    return {"status": "ok", "message": "Stock Screener API is running"}


# ---------------------------------------------------------------------------
# AI Research Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/ai/status")
async def ai_status():
    """Check if AI is configured and get active model."""
    return {"enabled": AI_ENABLED, "model": AI_MODEL if AI_ENABLED else None}


@app.get("/api/usage")
async def get_usage():
    """Get the current API usage stats for Gemini and Tavily."""
    return get_current_usage()


@app.post("/api/ai/upload")
async def ai_upload(ticker: str = Form(...), files: list[UploadFile] = File(...)):
    """Upload PDF documents for a ticker and send them to Gemini Files API."""
    if not AI_ENABLED:
        raise HTTPException(status_code=400, detail="AI Research assistant is not enabled.")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    try:
        safe_ticker = sanitize_ticker(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get existing session files
    from ai_research import get_session
    session = get_session(safe_ticker)
    existing_files = session.get("documents_used", [])

    # Calculate count of unique files (excluding replacements with the same name)
    new_filenames = [os.path.basename(f.filename or "") for f in files]
    unique_existing_files = [name for name in existing_files if name not in new_filenames]

    if len(unique_existing_files) + len(files) > 3:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Maximum 3 files can be uploaded in a session. You currently have {len(existing_files)} file(s) "
                f"in session. Uploading {len(files)} new file(s) would exceed the limit."
            )
        )

    ticker_temp_dir = safe_join(AI_TEMP_DIR, safe_ticker)
    os.makedirs(ticker_temp_dir, exist_ok=True)
    saved_paths = []

    for f in files:
        raw_filename = f.filename or ""
        safe_name = os.path.basename(raw_filename)
        if not safe_name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File '{safe_name}' is not a PDF. Only PDFs are supported.")

        file_path = safe_join(ticker_temp_dir, safe_name)
        try:
            content = await f.read()
            # 50MB limit validation
            if len(content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File '{safe_name}' exceeds the 50MB size limit.")

            with open(file_path, "wb") as out_file:
                out_file.write(content)
            saved_paths.append(file_path)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file '{safe_name}': {str(e)}")

    try:
        result = upload_documents(safe_ticker, saved_paths)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/analyze")
async def ai_analyze(request: dict):
    """Run document analysis for a ticker in a specified mode."""
    if not AI_ENABLED:
        raise HTTPException(status_code=400, detail="AI Research assistant is not enabled.")

    raw_ticker = request.get("ticker")
    mode = request.get("mode")

    if not raw_ticker or not mode:
        raise HTTPException(status_code=400, detail="Missing 'ticker' or 'mode' in request body.")

    try:
        safe_ticker = sanitize_ticker(raw_ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    context = request.get("context", {})

    try:
        result = analyze_documents(
            mode=mode,
            ticker=safe_ticker,
            context=context
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/ask")
async def ai_ask(request: dict):
    """Free-form session-scoped Q&A based on uploaded documents."""
    if not AI_ENABLED:
        raise HTTPException(status_code=400, detail="AI Research assistant is not enabled.")

    raw_ticker = request.get("ticker")
    question = request.get("question")

    if not raw_ticker or not question:
        raise HTTPException(status_code=400, detail="Missing 'ticker' or 'question' in request body.")

    try:
        safe_ticker = sanitize_ticker(raw_ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = analyze_documents(
            mode="qa",
            ticker=safe_ticker,
            question=question
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/reports/{ticker}")
async def ai_get_saved(ticker: str):
    """Get all saved reports for a ticker from local disk."""
    try:
        safe_ticker = sanitize_ticker(ticker)
        reports = get_saved_reports(safe_ticker)
        return reports
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/ai/session/{ticker}")
async def ai_clear_session_route(ticker: str):
    """Clear uploaded documents and active session references for a ticker."""
    try:
        safe_ticker = sanitize_ticker(ticker)
        result = clear_session(safe_ticker)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Discovery Lens Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/discovery/strategies")
async def api_get_strategies():
    """List all available strategies with their labels and descriptions."""
    from discovery_prompts import DISCOVERY_STRATEGIES
    # Strip prompt_template from response for size and clean separation
    cleaned_strategies = []
    for s in DISCOVERY_STRATEGIES:
        cleaned_strategies.append({
            "id": s["id"],
            "category": s.get("category", "core"),
            "name": s["name"],
            "description": s["description"],
            "input_label": s["input_label"],
            "input_type": s["input_type"],
            "required": s["required"]
        })
    return cleaned_strategies


@app.post("/api/discovery/run")
async def api_run_discovery(request: Request):
    """
    Run a discovery strategy in a streaming response.
    Returns a stream of JSON lines containing log updates and finally the result.
    """
    body = await request.json()
    strategy_id = body.get("strategy_id")
    user_input = body.get("user_input") or body.get("context") or ""

    if not strategy_id:
        raise HTTPException(status_code=400, detail="Missing 'strategy_id' in request body.")

    from discovery import run_discovery_strategy
    import queue
    import threading
    import asyncio

    q = queue.Queue()

    def log_callback(msg: str):
        q.put({"type": "progress", "message": msg})

    def worker():
        try:
            meta = run_discovery_strategy(strategy_id, user_input, log_callback)
            if hasattr(meta, "model_dump"):
                meta_dict = meta.model_dump()
            else:
                meta_dict = meta.dict()
            q.put({"type": "result", "data": meta_dict})
        except InterruptedError:
            logger.info("Discovery worker cancelled by user.")
            q.put({"type": "cancelled", "message": "Discovery stopped by user."})
        except Exception as e:
            logger.error("Error running discovery: %s", e)
            q.put({"type": "error", "message": str(e)})
        finally:
            q.put(None)  # Sentinel to end stream

    threading.Thread(target=worker, daemon=True).start()

    async def event_generator():
        try:
            while True:
                while q.empty():
                    if await request.is_disconnected():
                        from discovery import cancel_discovery
                        cancel_discovery()
                        logger.warning("Client disconnected from discovery stream. Stopped worker.")
                        return
                    await asyncio.sleep(0.1)
                item = q.get_nowait()
                if item is None:
                    break
                yield json.dumps(item) + "\n"
        except (asyncio.CancelledError, GeneratorExit):
            from discovery import cancel_discovery
            cancel_discovery()
            logger.warning("Discovery stream generator closed. Stopped worker.")
            return

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.post("/api/discovery/stop")
async def api_stop_discovery():
    """Stop/cancel any active discovery process immediately."""
    from discovery import cancel_discovery
    cancel_discovery()
    return {"status": "ok", "message": "Stop signal sent to active discovery run."}


@app.get("/api/discovery/saved")
async def api_get_saved_discoveries():
    """List all saved discoveries."""
    from discovery import get_saved_discoveries as load_summaries
    return load_summaries()


@app.get("/api/discovery/saved/{discovery_id}")
async def api_get_single_discovery(discovery_id: str):
    """Fetch details of a single saved discovery."""
    try:
        safe_id = validate_uuid(discovery_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from discovery import get_discovery
    meta = get_discovery(safe_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Discovery not found")
    return meta


@app.delete("/api/discovery/saved/{discovery_id}")
async def api_delete_single_discovery(discovery_id: str):
    """Delete a saved discovery."""
    try:
        safe_id = validate_uuid(discovery_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from discovery import delete_discovery
    success = delete_discovery(safe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Discovery not found or delete failed")
    return {"message": "Discovery deleted"}


# ---------------------------------------------------------------------------
# Master Synthesis Routes
# ---------------------------------------------------------------------------

@app.post("/api/synthesis/run")
async def api_run_synthesis(request: Request):
    """
    Run Master Synthesis over selected discovery IDs in a streaming response.
    Returns a stream of JSON lines containing progress and finally the result.
    """
    body = await request.json()
    raw_ids = body.get("discovery_ids", [])

    if not raw_ids or len(raw_ids) < 5:
        raise HTTPException(status_code=400, detail="Master Synthesis requires at least 5 selected strategy results.")

    try:
        discovery_ids = [validate_uuid(did) for did in raw_ids]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from synthesis import run_master_synthesis
    import queue
    import threading
    import asyncio

    q = queue.Queue()

    def progress_callback(msg: str):
        q.put({"type": "progress", "message": msg})

    def worker():
        try:
            meta = run_master_synthesis(discovery_ids, progress_callback)
            if hasattr(meta, "model_dump"):
                meta_dict = meta.model_dump()
            else:
                meta_dict = meta.dict()
            q.put({"type": "result", "data": meta_dict})
        except InterruptedError:
            logger.info("Synthesis worker cancelled by user.")
            q.put({"type": "cancelled", "message": "Master Synthesis stopped by user."})
        except Exception as e:
            logger.error("Error running master synthesis: %s", e)
            q.put({"type": "error", "message": str(e)})
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    async def event_generator():
        try:
            while True:
                while q.empty():
                    if await request.is_disconnected():
                        from synthesis import cancel_synthesis
                        cancel_synthesis()
                        logger.warning("Client disconnected from synthesis stream. Stopped worker.")
                        return
                    await asyncio.sleep(0.1)
                item = q.get_nowait()
                if item is None:
                    break
                yield json.dumps(item) + "\n"
        except (asyncio.CancelledError, GeneratorExit):
            from synthesis import cancel_synthesis
            cancel_synthesis()
            logger.warning("Synthesis stream generator closed. Stopped worker.")
            return

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.post("/api/synthesis/stop")
async def api_stop_synthesis():
    """Stop/cancel active synthesis run immediately."""
    from synthesis import cancel_synthesis
    cancel_synthesis()
    return {"status": "ok", "message": "Stop signal sent to active synthesis run."}


@app.get("/api/synthesis/saved")
async def api_get_saved_syntheses():
    """List all saved syntheses."""
    from synthesis import get_saved_syntheses as load_summaries
    return load_summaries()


@app.get("/api/synthesis/saved/{synthesis_id}")
async def api_get_single_synthesis(synthesis_id: str):
    """Fetch details of a single saved synthesis."""
    try:
        safe_id = validate_uuid(synthesis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from synthesis import get_synthesis
    meta = get_synthesis(safe_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Synthesis not found")
    return meta


@app.delete("/api/synthesis/saved/{synthesis_id}")
async def api_delete_single_synthesis(synthesis_id: str):
    """Delete a saved synthesis."""
    try:
        safe_id = validate_uuid(synthesis_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from synthesis import delete_synthesis
    success = delete_synthesis(safe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Synthesis not found or delete failed")
    return {"message": "Synthesis deleted"}


# ---------------------------------------------------------------------------
# Synthesis Chat & Verification Endpoints
# ---------------------------------------------------------------------------

class SynthesisChatRequest(BaseModel):
    synthesis_id: str
    user_message: str = ""
    action: str = "chat"        # "chat" or "generate_thesis"
    target_stock: str = ""      # Company name or ticker for thesis generation


@app.post("/api/synthesis/chat")
async def api_run_synthesis_chat(req: SynthesisChatRequest):
    """Stream AI responses for report-level synthesis chat verification & thesis generation."""
    from synthesis_chat import process_synthesis_chat

    def event_generator():
        for chunk in process_synthesis_chat(
            synthesis_id=req.synthesis_id,
            user_message=req.user_message,
            action=req.action,
            target_stock=req.target_stock
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.get("/api/synthesis/chat/{synthesis_id}")
async def api_get_synthesis_chat(synthesis_id: str):
    """Fetch existing report-level chat session for a synthesis report."""
    from synthesis_chat import get_synthesis_chat
    session = get_synthesis_chat(synthesis_id)
    if not session:
        return {"messages": [], "generated_thesis": None}
    return session


@app.delete("/api/synthesis/chat/{synthesis_id}")
async def api_delete_synthesis_chat(synthesis_id: str):
    """Delete report-level chat session for a synthesis report."""
    from synthesis_chat import delete_synthesis_chat
    success = delete_synthesis_chat(synthesis_id)
    return {"success": success}


def _fetch_yahoo_search(q: str) -> list[dict]:
    """Helper to query Yahoo Finance search API synchronously in worker thread."""
    import urllib.parse
    import urllib.request
    yf_matches = []
    try:
        quoted_q = urllib.parse.quote(q)
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={quoted_q}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
        
        for item in data.get("quotes", []):
            symbol = item.get("symbol", "")
            if symbol.endswith(".NS") or symbol.endswith(".BO"):
                clean_sym = symbol.split(".")[0]
                yf_matches.append({
                    "symbol": clean_sym,
                    "name": item.get("longname") or item.get("shortname") or clean_sym,
                    "sector": item.get("sector") or item.get("industry") or "NSE/BSE"
                })
    except Exception as e:
        logger.warning("Yahoo Finance search failed: %s", e)
    return yf_matches


@app.get("/api/stocks/search")
async def api_search_stocks(q: str = ""):
    """Search for stock tickers by company name or symbol without blocking the event loop."""
    import asyncio
    if not q:
        return []
    q_lower = q.lower().strip()
    
    # 1. Search local stocks list first (Nifty 500)
    local_matches = []
    try:
        all_stocks = get_nifty500_stocks()
        for s in all_stocks:
            sym = s.get("symbol", "")
            name = s.get("name", "")
            if q_lower in sym.lower() or q_lower in name.lower():
                local_matches.append({
                    "symbol": sym,
                    "name": name,
                    "sector": s.get("sector", "NSE")
                })
    except Exception as e:
        logger.warning("Local stock search failed: %s", e)
        
    # If we have enough matches, return them
    if len(local_matches) >= 10:
        return local_matches[:10]
        
    # 2. Query Yahoo Finance search API in a non-blocking threadpool worker
    yf_matches = await asyncio.to_thread(_fetch_yahoo_search, q)
        
    # Combine results and deduplicate by symbol
    seen = set()
    combined = []
    for s in local_matches + yf_matches:
        sym = s["symbol"]
        if sym not in seen:
            seen.add(sym)
            combined.append(s)
            
    return combined[:15]


