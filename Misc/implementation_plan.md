# Stock Screening & Analysis Tool — Final Build Plan

> **Quality + Reasonable Price + Margin of Safety**
> For Indian NSE stocks. No AI. 100% free. Runs locally.
> Your strategy research = the code. Nothing configurable in MVP.

---

## Pipeline

```
Universe (Nifty 500)
     ↓
Screening (quantitative filters)
     ↓
Quality Score (0-100)
     ↓
Intrinsic Value Range + Margin of Safety
     ↓
Governance Checklist (manual)
     ↓
Thesis Tracker
     ↓
Conviction Level (auto-calculated)
     ↓
Monitoring
     ↓
Postmortem (after exit)
```

---

## How It Works

```
1. nselib fetches Nifty 500 stock list             → FREE
2. yfinance fetches financials per stock            → FREE
3. Python calculates ratios, scores, valuations     → FREE
4. Browser displays dashboard with results          → FREE

No AI. No LLM. No API keys. No subscriptions. No settings to configure.
Strategy is hardcoded from your research. Runs on localhost:8000.
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  BROWSER (localhost:8000)                                 │
│  Dark theme — 4 pages                                    │
│  Dashboard | Screener | Analyzer | Thesis Board          │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  PYTHON BACKEND (FastAPI)                                 │
│                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Screener │ │ Analyzer │ │ Valuator │ │ Thesis &    │ │
│  │          │ │          │ │          │ │ Postmortem  │ │
│  │ • Scan   │ │ • Quality│ │ • Graham │ │ Manager     │ │
│  │   Nifty  │ │   Score  │ │   Number │ │             │ │
│  │   500    │ │ • Pass/  │ │ • Earn.  │ │ • Save      │ │
│  │ • Filter │ │   fail   │ │   Yield  │ │ • Load      │ │
│  │ • Rank   │ │   per    │ │ • DCF    │ │ • Edit      │ │
│  │          │ │   metric │ │   range  │ │ • Delete    │ │
│  └────┬─────┘ └────┬─────┘ └──────────┘ └─────────────┘ │
│       │            │                                      │
│       ▼            ▼                                      │
│  ┌──────────┐ ┌──────────┐                                │
│  │ nselib   │ │ yfinance │  Both FREE, no API key         │
│  └──────────┘ └──────────┘                                │
└──────────────────────────────────────────────────────────┘
```

---

## What Changed (v3 → Final)

| Removed / Simplified | Why |
|---|---|
| ~~Settings page~~ | Strategy hardcoded. No evidence to justify configurability yet. |
| ~~Valuation Score (0-100)~~ | Valuation is too uncertain for a single number. Show intrinsic value range instead. |
| ~~Weight sliders~~ | No evidence weights are optimal. Hardcode from research. Optimize after backtesting (Phase 2). |
| ~~Governance Score (6/8)~~ | False precision for qualitative judgment. Checklist only — checkmarks, no number. |
| ~~Beginner/Advanced toggle~~ | Only Beginner mode exists in MVP. Advanced = Phase 2 after real usage data. |

| Kept | Why |
|---|---|
| Quality Score (0-100) | Quality IS measurable from financial data. Weighted composite of 11 criteria. |
| Intrinsic Value Range | Honest: shows Conservative/Base/Optimistic + margin of safety %. |
| Governance Checklist | Manual checkmarks — critical for Indian market. No fake score. |
| Thesis + Postmortem | Most valuable long-term features. Your investing journal. |
| Sector awareness | Hardcoded sector rules — different thresholds for different industries. |
| Conviction labels | Auto-calculated from Quality Score + Margin of Safety. |

---

## Quality Score (0-100)

Weighted composite of 11 criteria. All weights hardcoded.

| # | Criterion | Threshold | Weight | Sector-Adjusted? |
|---|---|---|---|---|
| 1 | Market cap | > ₹4,000 Cr | **Gate** (must pass) | No |
| 2 | Earnings consistency | Positive NI all available years | 3x | No |
| 3 | FCF consistency | Positive FCF 3+ of 4 years | 3x | No |
| 4 | ROIC | > 12% avg | **4x** | Yes |
| 5 | ROE | > 15% | 3x | Yes |
| 6 | Debt-to-Equity | < 1.0 | 2x | **Yes** |
| 7 | Debt coverage | LT debt < 5× avg FCF | 2x | Yes |
| 8 | Current ratio | > 1.5 | 1x | **Yes** |
| 9 | Share dilution | Stable/decreasing | 2x | No |
| 10 | Operating margins | > 10% | 2x | **Yes** |
| 11 | FCF ≈ Net Income | Ratio 0.7 – 1.5 | 2x | No |

**Total max weight: 28x → normalized to 0-100**

### Hardcoded Sector Rules

| Sector Group | D/E | Current Ratio | Margins |
|---|---|---|---|
| IT / Software | <1.0 | >1.5 | >15% |
| FMCG / Consumer | <1.0 | >1.0 | >10% |
| Pharma | <1.0 | >1.5 | >12% |
| Industrial | <1.5 | >1.5 | >8% |
| Financial / Banking | **Flagged** | **Flagged** | **Flagged** |
| Utilities / Energy | <2.0 | >1.0 | >8% |

> Financial sector stocks display: *"Standard screening criteria do not apply to banks/NBFCs. Sector-specific analysis module planned for Phase 2."*

---

## Valuation Display (Not a Score)

Instead of collapsing valuation into a single number, show the actual data:

```
┌─────────────────────────────────────────────┐
│  📊 VALUATION                               │
│                                             │
│  Graham Number:        ₹1,180               │
│  Earnings Yield:       7.2% (vs RFR: 6.5%) │
│  PEG Ratio:            0.85 ⚠️ supplementary│
│                                             │
│  DCF (Supplementary):                       │
│  Assumptions: Growth 8% | Discount 12%     │
│  🐻 Conservative:  ₹900  (Growth: 5%)      │
│  📊 Base:          ₹1,200 (Growth: 8%)      │
│  🐂 Optimistic:    ₹1,500 (Growth: 12%)    │
│                                             │
│  Current Price:    ₹1,050                   │
│                                             │
│  Margin of Safety (vs Graham #):  +11%      │
│  Margin of Safety (vs DCF Bear):  -14% ⚠️  │
│  Margin of Safety (vs DCF Base):  +12.5%   │
│                                             │
│  ⚠️ Valuation is an estimate, not a         │
│  guarantee. DCF is sensitive to             │
│  assumptions. Cross-check with annual       │
│  reports.                                   │
└─────────────────────────────────────────────┘
```

**Margin of Safety for conviction logic** uses the most conservative estimate:
- `min(Graham Number, DCF Conservative)` vs current price

---

## Conviction Logic

Auto-calculated. No manual input needed.

```python
margin_of_safety = (conservative_intrinsic - current_price) / conservative_intrinsic

if quality_score >= 70 and margin_of_safety >= 0.25:
    status = "Strong Candidate"
elif quality_score >= 70 and margin_of_safety >= 0:
    status = "Candidate"
elif quality_score >= 70 and margin_of_safety < 0:
    status = "Watchlist"  # Great business, too expensive
elif quality_score >= 40 and margin_of_safety >= 0.25:
    status = "Needs Work"  # Cheap, but verify quality
else:
    status = "Avoid"
```

| Quality Score | Margin of Safety | Conviction | Meaning |
|---|---|---|---|
| ≥70 | ≥25% | **Strong Candidate** | Quality business at a bargain |
| ≥70 | 0-25% | **Candidate** | Quality business, reasonable price |
| ≥70 | <0% (overpriced) | **Watchlist** | Great business, wait for better price |
| 40-69 | ≥25% | **Needs Work** | Cheap but quality uncertain |
| <40 | Any | **Avoid** | Insufficient quality |

---

## Governance Checklist (No Score)

Manual checkmarks only. Located as a tab in Analyzer.

```
☐ Promoter holding > 50%?
☐ Promoter pledge < 10% (or zero)?
☐ Promoter holding stable/increasing?
☐ Big-4 or reputable auditor?
☐ Related-party transactions minimal?
☐ No contingent liability red flags?
☐ Rational capital allocation?
☐ No frequent equity dilution?
```

No numerical score. User reads annual reports and checks/unchecks.

---

## Thesis Tracker

```
┌─────────────────────────────────────────┐
│  📝 THESIS: TCS.NS                      │
│                                         │
│  Why I'm interested:                    │
│  [Free text]                            │
│                                         │
│  What would make me wrong:              │
│  [Free text]                            │
│                                         │
│  I would sell if:                       │
│  [Free text]                            │
│                                         │
│  Key metrics when added:               │
│  Quality: 82 | Price: ₹3,800           │
│  MoS: +18% | Date: 2026-06-15          │
└─────────────────────────────────────────┘
```

---

## Postmortem Tracker

```
┌─────────────────────────────────────────┐
│  📋 POSTMORTEM: RELIANCE.NS             │
│                                         │
│  Entry: 2026-06-15 | ₹2,800            │
│  Exit:  2027-03-10 | ₹3,200            │
│  Return: +14.3%                         │
│                                         │
│  Why I bought: [original thesis]        │
│  Why I sold:   [free text]              │
│  Was thesis right? [free text]          │
│  Key lessons:  [free text]              │
│  Mistakes:     [free text]              │
└─────────────────────────────────────────┘
```

---

## Data Disclaimer (shown on every analysis)

> ⚠️ **Financial history limited to ~4 years (yfinance).** This is insufficient for full Graham-style 10-year analysis. Cross-check against Screener.in or annual reports. Phase 2 will add 10-year data.

---

## Pages (4 total)

| Page | What it shows |
|---|---|
| **Dashboard** | Overview — recent scans, thesis count, quick stats |
| **Screener** | Scan Nifty 500 → ranked table: ticker, sector, Quality Score, margin of safety %, conviction label |
| **Analyzer** | Deep dive on one stock. 3 tabs: **Scorecard** (quality metrics + pass/fail), **Valuation** (intrinsic value range + MoS), **Governance** (checklist). Plus thesis creation form and trend charts. |
| **Thesis Board** | All saved theses + postmortems. Your investing journal. |

### Design System
- **Theme:** Dark mode, glassmorphism cards
- **Background:** Deep navy (#0a0e1a)
- **Accent:** Cyan (#00d4ff) → Purple (#a855f7) gradient
- **Quality score:** Blue gradient bar
- **Margin of Safety:** Green (positive) / Red (negative)
- **Pass/Fail:** Green (#00d4aa) / Red (#ff4757) / Amber (#ffa502)
- **Conviction colors:** Cyan (Strong Candidate), Green (Candidate), Amber (Watchlist/Needs Work), Red (Avoid)
- **Typography:** Inter (Google Fonts)

---

## Project Structure

```
stock-screener/
├── backend/
│   ├── main.py              # FastAPI app + all routes + static file serving
│   ├── data_fetcher.py      # yfinance + nselib: fetch, cache, normalize
│   ├── screener.py          # Bulk scan: Quality Score + conviction for all stocks
│   ├── analyzer.py          # Single stock: detailed Quality Score breakdown
│   ├── valuator.py          # Graham Number, Earnings Yield, DCF range, PEG, MoS
│   ├── thesis.py            # Thesis + Postmortem CRUD (JSON file storage)
│   ├── config.py            # ALL hardcoded thresholds, weights, sector rules
│   ├── models.py            # Pydantic response models
│   └── requirements.txt     # fastapi, uvicorn, yfinance, nselib, pandas
├── frontend/
│   ├── index.html           # SPA shell + sidebar nav
│   ├── css/
│   │   └── styles.css       # Complete design system
│   ├── js/
│   │   ├── app.js           # Hash-based router + page init
│   │   ├── dashboard.js     # Dashboard page logic
│   │   ├── screener.js      # Screener: trigger scan, display table, sort/filter
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

**Total files to create: 17**

---

## API Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/stocks` | Nifty 500 stock list |
| POST | `/api/screen` | Bulk scan → ranked results with Quality Score + MoS + conviction |
| GET | `/api/stock/{ticker}` | Full analysis: quality breakdown + valuation + conviction |
| GET | `/api/theses` | List all saved theses |
| POST | `/api/thesis` | Create or update a thesis |
| DELETE | `/api/thesis/{ticker}` | Delete a thesis |
| GET | `/api/postmortems` | List all postmortems |
| POST | `/api/postmortem` | Create a postmortem |

**8 routes. Simple.**

---

## Verification Plan

```bash
# Install
cd stock-screener
pip install -r backend/requirements.txt

# Run
cd backend
uvicorn main:app --reload --port 8000

# Open: http://localhost:8000
```

**Manual checks:**
1. Analyze RELIANCE.NS → compare metrics with Screener.in
2. Analyze TCS.NS → manually calculate Graham Number, verify match
3. Run full Nifty 500 scan → check that ranking makes intuitive sense
4. Create thesis → reload → verify persistence
5. Financial sector stock → verify "criteria don't apply" flag appears

---

## Phases

| Phase | What | When |
|---|---|---|
| **MVP (now)** | Dashboard + Screener + Analyzer + Thesis Board | Build now |
| **Phase 2** | Backtesting, Screener.in 10yr data, Financial sector module | After MVP tested |
| **Phase 3** | Settings/configurability, Portfolio tracker, Position sizing, PDF export | After backtesting evidence |
