# StockLens — Stock Screening & Analysis Tool

> **Quality + Reasonable Price + Margin of Safety**
> For Indian NSE stocks. No AI. 100% free. Runs locally.

---

## What is StockLens?

StockLens is a locally-run stock screening and fundamental analysis tool for Indian equities (NSE).
It evaluates stocks using a quality-based scoring system inspired by value investing principles
(Graham, Buffett, Lynch, Greenblatt, Klarman, Damodaran) and provides valuation estimates
with margin of safety calculations.

**No AI/LLM. No API keys. No subscriptions. Pure data + math.**

---

## Features

| Feature | Description |
|---|---|
| **Quality Score (0-100)** | Weighted composite of 11 fundamental criteria |
| **Intrinsic Value Range** | Graham Number, Earnings Yield, DCF (Bear/Base/Bull) |
| **Margin of Safety** | Conservative estimate vs current market price |
| **Conviction Labels** | Auto-calculated: Strong Candidate / Candidate / Watchlist / Needs Work / Avoid |
| **Governance Checklist** | Manual checkmarks for qualitative checks (promoter, auditor, etc.) |
| **Thesis Tracker** | Record why you're interested, what would make you wrong, sell conditions |
| **Postmortem Tracker** | After selling, record lessons learned and decision quality |
| **Sector Awareness** | Different thresholds for IT, FMCG, Pharma, Industrial, Utilities |
| **Financial Sector Flag** | Banks/NBFCs flagged — standard criteria don't apply |

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
| **Dashboard** | Overview — thesis count, postmortem count, quick stats |
| **Screener** | Scan Nifty 50/500 → ranked table with Quality Score, MoS%, conviction |
| **Analyzer** | Deep dive: Scorecard (11 criteria), Valuation (Graham/DCF/PEG), Governance, Thesis form |
| **Thesis Board** | All saved theses + postmortems. Your investing journal. |

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
│   ├── main.py              # FastAPI app + routes + static file serving
│   ├── data_fetcher.py      # yfinance + nselib: fetch, cache, normalize
│   ├── screener.py          # Quality Score checks + conviction logic
│   ├── analyzer.py          # Single stock detailed analysis
│   ├── valuator.py          # Graham Number, Earnings Yield, DCF, PEG, MoS
│   ├── thesis.py            # Thesis + Postmortem CRUD (JSON file storage)
│   ├── config.py            # ALL hardcoded thresholds, weights, sector rules
│   ├── models.py            # Pydantic response models
│   └── requirements.txt     # fastapi, uvicorn, yfinance, nselib, pandas
├── frontend/
│   ├── index.html           # SPA shell + sidebar nav
│   ├── css/
│   │   └── styles.css       # Complete design system (dark, glassmorphism)
│   ├── js/
│   │   ├── app.js           # Hash-based router + page init
│   │   ├── dashboard.js     # Dashboard page logic
│   │   ├── screener.js      # Screener: scan, table, sort, universe select
│   │   ├── analyzer.js      # Analyzer: scorecard + valuation + governance + thesis
│   │   ├── thesis.js        # Thesis board + postmortem views
│   │   ├── charts.js        # Chart.js trend chart configs
│   │   └── utils.js         # ₹/Cr formatters, DOM helpers, API calls
│   └── assets/
├── data/
│   ├── cache/               # Cached yfinance data (JSON, 24hr TTL)
│   ├── theses/              # Saved thesis documents (JSON per stock)
│   └── postmortems/         # Saved postmortem documents (JSON)
└── README.md
```

---

## API Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/stocks` | Nifty 500 stock list |
| POST | `/api/screen` | Bulk scan → ranked results |
| GET | `/api/stock/{ticker}` | Full analysis for one stock |
| GET | `/api/theses` | List all saved theses |
| POST | `/api/theses` | Create or update a thesis |
| DELETE | `/api/theses/{ticker}` | Delete a thesis |
| GET | `/api/postmortems` | List all postmortems |
| POST | `/api/postmortems` | Create a postmortem |

---

## Data Sources

| Source | What | Cost |
|---|---|---|
| **yfinance** | Income statement, balance sheet, cash flow, key ratios, price | Free |
| **nselib** | Nifty 500 stock list | Free |

> ⚠️ Financial history is limited to ~4 years via yfinance. Cross-check with annual reports.

---

## Phases

| Phase | What |
|---|---|
| **MVP (current)** | Dashboard + Screener + Analyzer + Thesis Board |
| **Phase 2** | Backtesting, Screener.in 10yr data, Financial sector module |
| **Phase 3** | Settings/configurability, Portfolio tracker, Position sizing, PDF export |

---

## Disclaimer

This tool is for **educational and analytical purposes only**. It is NOT investment advice.
Always do your own research before making investment decisions. The tool is your research
analyst, not your portfolio manager.
