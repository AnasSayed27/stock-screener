# StockLens — Stock Screening & Analysis Platform

> **Quality + Reasonable Price + Margin of Safety + Autonomous AI Research**
> For Indian NSE stocks. Hybrid architecture: Pure Math Quant Engine + Agentic AI Discovery. Runs locally.

---

## What is StockLens?

StockLens is an equity screening, fundamental valuation, and autonomous research platform for Indian equities (NSE).
It operates on a **dual-engine architecture**:
1. **Deterministic Quantitative Core**: Evaluates stocks using a quality-based scoring system inspired by classic value investing principles (Graham, Buffett, Lynch, Greenblatt, Klarman, Damodaran) and provides intrinsic valuation ranges (Graham Number, 3-Scenario DCF, PEG, Margin of Safety). **Pure data + math — zero hallucinations.**
2. **Autonomous Agentic Discovery Core**: A multi-turn AI research loop powered by Google Gemini and Tavily Search that autonomously scours unstructured disclosures, filings, and web intelligence across 10 specialized strategies, with cross-strategy Master Synthesis and adversarial thesis verification.

---

## Features

| Feature | Category | Description |
|---|---|---|
| **Quality Score (0-100)** | Quantitative | Weighted composite of 11 fundamental criteria across 4 years |
| **Intrinsic Value Range** | Quantitative | Graham Number, Earnings Yield, DCF (Bear/Base/Bull), PEG |
| **Margin of Safety (MoS %)** | Quantitative | Conservative estimate vs current market price |
| **Conviction Labels** | Quantitative | Auto-calculated: Strong Candidate / Candidate / Watchlist / Needs Work / Avoid |
| **Sector Awareness** | Quantitative | Hardcoded thresholds for IT, FMCG, Pharma, Industrial, Utilities |
| **Financial Sector Flag** | Quantitative | Banks & NBFCs flagged (standard criteria excluded) |
| **Governance Checklist** | Qualitative | 8-point manual audit (promoter pledging, auditor changes, etc.) |
| **Agentic DiscoveryLens** | AI Research | 5-phase autonomous research loop with web & financial tool calling |
| **Master Synthesis** | AI Research | Cross-strategy correlation engine over $\ge 7$ discovery runs |
| **AI Document Assistant** | AI Research | Up to 3 PDF annual reports analyzed via Gemini Files API |
| **Thesis & Postmortem Tracker** | Journal | Full investment thesis logging and post-exit decision retrospective |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Internet connection (for fetching stock data)

### Install

```bash
cd stock-screener
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r backend/requirements.txt
```

### Run

```bash
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

### Open

```
http://localhost:8000
```

---

## Pages

| Page | Purpose |
|---|---|
| **Dashboard** | Overview — thesis count, postmortem count, quick stats, API usage |
| **Discovery** | Autonomous agentic research across 10 specialized strategies + Master Synthesis |
| **Screener** | Scan Nifty 50/500/Midcap/Smallcap/F&O → ranked table with Quality Score, MoS%, conviction |
| **Analyzer** | Deep dive: Scorecard (11 criteria), Valuation (Graham/DCF/PEG), Governance, AI PDF Research, Thesis form |
| **Thesis Board** | All saved theses + postmortems. Your disciplined investing journal. |

---

## Quality Score Criteria

| # | Criterion | Threshold | Weight |
|---|---|---|---|
| 1 | Market Cap | > ₹4,000 Cr | Gate (must pass) |
| 2 | ROIC | > 12% avg | 4× |
| 3 | ROE | > 15% | 3× |
| 4 | Earnings Consistency | All years positive NI | 3× |
| 5 | FCF Consistency | 3+/4 years positive | 3× |
| 6 | Debt-to-Equity | < 1.0 | 2× |
| 7 | Debt Coverage | < 5× avg FCF | 2× |
| 8 | Current Ratio | > 1.5 | 1× |
| 9 | Operating Margins | > 10% | 2× |
| 10 | Share Dilution | Stable/decreasing | 2× |
| 11 | FCF/NI Ratio | 0.7 – 1.5 | 2× |
| 12 | Earnings Yield | > 6% | 3× |

---

## Project Structure

```
stock-screener/
├── backend/
│   ├── main.py              # FastAPI app + routes + NDJSON streaming + static serving
│   ├── data_fetcher.py      # yfinance + nselib: fetch, disk cache, normalize
│   ├── screener.py          # 11 Quality Score checks + conviction classification
│   ├── analyzer.py          # Single stock detailed scorecard assembly
│   ├── valuator.py          # Graham Number, Earnings Yield, 3-scenario DCF, PEG, MoS
│   ├── thesis.py            # Thesis + Postmortem CRUD (JSON file storage)
│   ├── config.py            # All thresholds, weights, sector overrides, AI models
│   ├── models.py            # Pydantic schemas for Screener, Discovery & Synthesis
│   ├── discovery.py         # Core agentic discovery loop + tool execution + streaming
│   ├── discovery_phases.py  # 5 research phase definitions + Evaluator-Critic prompts
│   ├── discovery_prompts.py # 10 investment discovery strategies & system prompts
│   ├── discovery_tools.py   # Web search (Tavily) & financial data agent tools
│   ├── synthesis.py         # Cross-strategy Master Synthesis engine (≥7 strategies)
│   ├── synthesis_chat.py    # Report-level thesis verification & adversarial Q&A
│   ├── ai_research.py       # PDF Annual Report RAG via Gemini Files API
│   ├── usage_tracker.py     # Gemini & Tavily API rate limit and quota tracker
│   ├── storage.py           # Atomic, crash-safe JSON writes (mkstemp + fsync + replace)
│   ├── security_utils.py    # Path traversal guards, ticker & UUID sanitizers
│   └── requirements.txt     # fastapi, uvicorn, yfinance, nselib, google-genai, etc.
├── frontend/
│   ├── index.html           # SPA shell + responsive sidebar + API usage widget
│   ├── css/
│   │   └── styles.css       # Complete dark-mode glassmorphism design system
│   ├── js/
│   │   ├── app.js           # Hash router + page initialization & lifecycle
│   │   ├── dashboard.js     # Dashboard metrics + quick-action launcher
│   │   ├── screener.js      # Screener table, universe filter, sort, conviction badges
│   │   ├── analyzer.js      # Scorecard, valuation cards, governance, AI PDF upload & Q&A
│   │   ├── discovery.js     # DiscoveryLens runner, streaming NDJSON logs, Master Synthesis
│   │   ├── thesis.js        # Thesis board + postmortem CRUD views
│   │   ├── charts.js        # Chart.js trend configs (historical metrics & DCF)
│   │   └── utils.js         # ₹/Cr currency formatters, DOM helpers, toast alerts
│   └── assets/
├── data/
│   ├── cache/               # Cached yfinance financial statements (JSON, 24hr TTL)
│   ├── theses/              # Saved thesis documents (atomic JSON per stock)
│   ├── postmortems/         # Saved postmortem review documents (atomic JSON)
│   ├── discovery/           # Saved agentic discovery strategy runs
│   ├── synthesis/           # Saved Master Synthesis reports
│   ├── synthesis_chats/     # Saved adversarial verification chat sessions
│   └── ai_reports/          # Saved PDF extraction reports
├── tests/                   # Pytest suite (routes, discovery tools, screener, storage security)
└── README.md
```

---

## API Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/stocks` | Stock universe symbols (Nifty 50, 500, Midcap, Smallcap, F&O) |
| GET | `/api/stocks/search` | Fast ticker/company search with local + Yahoo fallback |
| POST | `/api/screen` | Bulk scan → ranked results (supports client disconnect abort) |
| GET | `/api/stock/{ticker}` | Comprehensive fundamental analysis & scorecard |
| GET/POST | `/api/theses` | List, create, or update investment theses |
| DELETE | `/api/theses/{ticker}` | Delete an investment thesis |
| GET/POST | `/api/postmortems` | List or create postmortem retrospective logs |
| GET | `/api/ai/status` | Check Gemini AI configuration & active model |
| POST | `/api/ai/upload` | Upload PDF reports (Annual Reports, DRHP) to Gemini Files API |
| POST | `/api/ai/analyze` | Run document extraction (governance, moat, risks, concall) |
| POST | `/api/ai/ask` | Session-scoped Q&A over uploaded PDF documents |
| GET | `/api/discovery/strategies` | List 10 available investment discovery strategies |
| POST | `/api/discovery/run` | Run 5-phase agent loop with streaming NDJSON logs |
| POST | `/api/discovery/stop` | Immediate cancellation signal for running discovery |
| GET | `/api/discovery/saved` | List all saved discovery strategy runs |
| POST | `/api/synthesis/run` | Run Master Synthesis over selected discovery runs (streaming NDJSON) |
| POST | `/api/synthesis/chat` | Adversarial thesis verification & buy/sell checklist generator |
| GET | `/api/usage` | Real-time Gemini and Tavily API quota & token usage stats |

---

## Data & Intelligence Sources

| Source | Role | Cost / Tier |
|---|---|---|
| **yfinance** | Audited financial statements (4 yrs), ratios, live quotes | Free |
| **nselib** | Official NSE India stock indexes (Nifty 50, 500, etc.) | Free |
| **Google Gemini API** | Multi-phase agent reasoning, PDF document parsing, synthesis | Free tier / Paid API key |
| **Tavily Search API** | Real-time web search for financial news, concalls, order books | Free tier / Paid API key |

> ⚠️ Financial history is limited to ~4 years via yfinance. Cross-check with annual reports.

---

## Architecture Evolution

| Layer | Implementation | Core Value |
|---|---|---|
| **Deterministic Quant Engine** | Pure Python math, 11 weighted gates, DCF/Graham/MoS | Uncompromising mathematical integrity, 0 hallucinations |
| **Agentic AI Discovery Engine** | 5-Phase research loop with tool calls & Master Synthesis | Unearths inflection points & market catalysts from web/filings |
| **Hardened System Engineering** | Atomic file writes, client-disconnect cancellation, NDJSON | High reliability, zero corrupted data, resource efficiency |

---

## Disclaimer

This tool is for **educational and analytical purposes only**. It is NOT investment advice.
Always do your own research before making investment decisions. The tool is your research
analyst, not your portfolio manager.
