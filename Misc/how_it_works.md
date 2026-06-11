# How Your Stock Screening Tool Works — Complete Guide

> A step-by-step explanation of what happens when you use the app.

---

## Starting the App

```
You open terminal → type: uvicorn main:app --port 8000
You open browser  → go to: localhost:8000
```

The app runs locally on your computer. No internet hosting. No login. No account. No cost. Just you and your PC.

Internet is only used to fetch stock data from Yahoo Finance and NSE. Everything else — all calculations, all storage — happens on your machine.

---

## Page 1: Dashboard

### What you see

A clean dark homepage showing:

- How many stocks you've scanned recently
- How many theses you've saved
- How many postmortems you've written
- A quick-start button: "Run Screener"

### What happens behind the scenes

Nothing complex. The app reads saved JSON files from your local `data/` folder and displays counts. No internet calls.

---

## Page 2: Screener

### Purpose

> "Show me all quality stocks in Nifty 500, ranked."

### What you do

Click "Run Scan."

### What happens — step by step

**Step 1 — Get the stock list**

```
Your app calls nselib (Python library)
    ↓
nselib goes to NSE India's website
    ↓
Returns list of ~500 Nifty stocks:
    RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, ...
```

**Step 2 — Fetch financial data (one stock at a time, 1 per second)**

```
For EACH stock:
    Your app calls yfinance("RELIANCE.NS")
        ↓
    yfinance goes to Yahoo Finance
        ↓
    Returns:
        - Income statement (4 years)
        - Balance sheet (4 years)
        - Cash flow statement (4 years)
        - Key ratios (P/E, ROE, D/E, etc.)
        - Current price
        ↓
    Saves to cache/ folder
    (so next time it loads instantly)
```

**Step 3 — Calculate Quality Score (pure math, no AI)**

```
For EACH stock, Python does arithmetic:

    debt_to_equity = total_debt / total_equity
    Is it < 1.0?  → ✅ pass (earns 2 weight points)

    roic = nopat / invested_capital
    Is it > 12%?  → ✅ pass (earns 4 weight points)

    roe = net_income / equity
    Is it > 15%?  → ✅ pass (earns 3 weight points)

    ... repeat for all 11 criteria ...

    Quality Score = total_points / max_points × 100
```

**Step 4 — Calculate valuation (pure math)**

```
Graham Number = √(22.5 × EPS × Book Value Per Share)

Margin of Safety = (Graham Number - Current Price) / Graham Number × 100%
```

**Step 5 — Assign conviction label**

```
Quality ≥ 70  AND  Margin of Safety ≥ 25%  →  "Strong Candidate"
Quality ≥ 70  AND  Margin of Safety 0-25%  →  "Candidate"
Quality ≥ 70  AND  Margin of Safety < 0%   →  "Watchlist"
Quality 40-69 AND  Margin of Safety ≥ 25%  →  "Needs Work"
Quality < 40                               →  "Avoid"
```

### What you see

A ranked table:

```
┌────────┬─────────────┬─────────┬───────────┬──────────────────┐
│ Ticker │ Sector      │ Quality │ Margin of │ Conviction       │
│        │             │  Score  │  Safety   │                  │
├────────┼─────────────┼─────────┼───────────┼──────────────────┤
│ TCS    │ IT          │  87     │  +28%     │ Strong Candidate │
│ PIDIND │ Industrial  │  79     │  +31%     │ Strong Candidate │
│ NESTL  │ FMCG        │  82     │  +8%      │ Candidate        │
│ ASIAN  │ Consumer    │  76     │  -12%     │ Watchlist         │
│ HDFC   │ Financial   │  --     │  --       │ Flagged ⚠️       │
│ VEDL   │ Industrial  │  35     │  +45%     │ Avoid            │
└────────┴─────────────┴─────────┴───────────┴──────────────────┘
```

You can sort by Quality Score, Margin of Safety, or Sector.

### Timing

- First scan: ~8-10 minutes (500 stocks × 1 per second)
- After first scan: instant (data is cached for 24 hours)

---

## Page 3: Analyzer

### Purpose

> "Deep dive into one stock. Is it actually worth investing in?"

### What you do

Click on "TCS" from the screener table, or search for any ticker.

### What happens

The app fetches TCS data (from cache or yfinance) and runs full analysis. Three tabs are displayed.

---

### Tab 1: Scorecard

Every criterion shown with pass/fail, actual value, threshold, and weight:

```
┌──────────────────────────────────────────────────┐
│  📊 QUALITY SCORECARD — TCS.NS                    │
│                                                    │
│  Quality Score: 87/100  ████████▋                  │
│                                                    │
│  ✅ ROIC:           38.2%    (threshold: >12%)  4x │
│  ✅ ROE:            42.1%    (threshold: >15%)  3x │
│  ✅ Earnings:       4/4 yrs positive            3x │
│  ✅ FCF:            4/4 yrs positive            3x │
│  ✅ D/E:            0.08     (threshold: <1.0)  2x │
│  ✅ Debt coverage:  0.3 yrs  (threshold: <5yr)  2x │
│  ✅ Current ratio:  2.8      (threshold: >1.5)  1x │
│  ✅ Op. margins:    25.1%    (threshold: >15%)  2x │
│  ✅ Share dilution: Stable                      2x │
│  ✅ FCF/NI ratio:   1.05     (threshold: 0.7-1.5) 2x│
│  ❌ Earnings Yield: 4.1%     (threshold: >6%)   3x │
│                                                    │
│  ⚠️ Data limited to ~4 years (yfinance).          │
└──────────────────────────────────────────────────┘
```

Below the scorecard: **trend charts** showing Revenue, Net Income, FCF, and Debt plotted over 4 years using Chart.js.

---

### Tab 2: Valuation

The actual intrinsic value calculations — no single score, just honest numbers:

```
┌──────────────────────────────────────────────────┐
│  💰 VALUATION — TCS.NS                           │
│                                                    │
│  Graham Number:      ₹3,950                       │
│  Earnings Yield:     4.1%  (Risk-free rate: 6.5%) │
│  PEG Ratio:          2.1   ⚠️ supplementary only  │
│                                                    │
│  DCF (Supplementary):                             │
│  Assumptions: Growth 8% | Discount 12%           │
│  Terminal Growth: 3%                              │
│  🐻 Conservative:  ₹3,200  (growth: 5%)          │
│  📊 Base:          ₹3,800  (growth: 8%)           │
│  🐂 Optimistic:    ₹4,500  (growth: 12%)         │
│                                                    │
│  Current Price:     ₹3,100                        │
│                                                    │
│  ▓▓▓▓▓▓▓▓░░░░  Price vs Range                    │
│  ₹3,100        ₹3,200    ₹3,800     ₹4,500       │
│  ▲ You are here                                   │
│                                                    │
│  Margin of Safety (vs Graham):    +21.5%          │
│  Margin of Safety (vs DCF Bear):  +3.1%           │
│                                                    │
│  ⚠️ DCF is sensitive to assumptions.              │
│  Use as supplementary only.                       │
└──────────────────────────────────────────────────┘
```

### How each calculation works

**Graham Number:**

```
graham = √(22.5 × EPS × Book Value Per Share)
graham = √(22.5 × 110 × 630)
graham = √(1,559,250)
graham = ₹3,950
```

**Margin of Safety:**

```
margin = (intrinsic - price) / intrinsic × 100
margin = (3950 - 3100) / 3950 × 100
margin = +21.5%
```

**DCF (simplified):**

```
Take last year's Free Cash Flow per share: ₹380

Project 10 years at assumed growth rate, discount to present value:
  Year 1:  380 × 1.08 = 410  → discounted: 410 / 1.12¹  = 366
  Year 2:  410 × 1.08 = 443  → discounted: 443 / 1.12²  = 353
  Year 3:  443 × 1.08 = 478  → discounted: 478 / 1.12³  = 340
  ... repeat for 10 years ...

Add terminal value (perpetual growth at 3% after year 10)
Sum everything = ₹3,800 (base case)

Run same math at 5% growth = ₹3,200 (conservative)
Run same math at 12% growth = ₹4,500 (optimistic)
```

**Earnings Yield:**

```
earnings_yield = EBIT / Enterprise Value × 100
```

**PEG Ratio:**

```
peg = (Price / EPS) / Earnings Growth Rate
peg = 28.2 / 13.5 = 2.1

PEG < 1.0 = cheap relative to growth
PEG > 2.0 = expensive relative to growth

⚠️ Flagged as supplementary — unreliable for cyclical stocks
```

---

### Tab 3: Governance Checklist

Manual checkboxes. You fill these after reading annual reports or Screener.in:

```
┌──────────────────────────────────────────┐
│  🏛️ GOVERNANCE CHECK — TCS.NS            │
│                                          │
│  ☑ Promoter holding > 50%?              │
│  ☑ Promoter pledge < 10% (or zero)?    │
│  ☑ Promoter holding stable/increasing? │
│  ☑ Big-4 or reputable auditor?         │
│  ☑ Related-party transactions minimal? │
│  ☐ No contingent liability red flags?  │
│  ☑ Rational capital allocation?        │
│  ☑ No frequent equity dilution?        │
│                                          │
│  These are YOUR manual checks based on   │
│  annual reports. No numerical score —    │
│  just honest checkmarks.                 │
└──────────────────────────────────────────┘
```

No score calculated. Governance is too qualitative for a number.

---

### Conviction Label (shown at top of Analyzer)

Auto-calculated from Quality Score + Margin of Safety:

```
Quality: 87  |  MoS (conservative): +3.1%  |  → CANDIDATE
"Quality business. Price is close to fair value."
```

---

### Thesis Form (at bottom of Analyzer)

If this stock interests you, record your reasoning:

```
┌──────────────────────────────────────────┐
│  📝 Save Thesis                          │
│                                          │
│  Why I'm interested:                     │
│  ┌────────────────────────────────────┐  │
│  │ High ROIC (38%), dominant IT       │  │
│  │ services company, sticky clients,  │  │
│  │ strong dividend history...         │  │
│  └────────────────────────────────────┘  │
│                                          │
│  What would make me wrong:               │
│  ┌────────────────────────────────────┐  │
│  │ AI replacing traditional IT        │  │
│  │ services, margin compression from  │  │
│  │ competition...                     │  │
│  └────────────────────────────────────┘  │
│                                          │
│  I would sell if:                        │
│  ┌────────────────────────────────────┐  │
│  │ ROIC drops below 20%, major client │  │
│  │ loss, management integrity issue   │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [💾 Save Thesis]                        │
└──────────────────────────────────────────┘
```

Clicking Save stores this as a JSON file on your PC with a snapshot of the current metrics (Quality Score, Price, Margin of Safety, Date).

---

## Page 4: Thesis Board

### Purpose

> "Your investing journal. All theses and postmortems in one place."

### What you see

```
┌──────────────────────────────────────────────────┐
│  📋 THESIS BOARD                                  │
│                                                    │
│  Active Theses (3)                                │
│  ┌──────────┬────────┬────────┬─────────────────┐│
│  │ TCS      │ Q: 87  │ +3.1% │ Candidate        ││
│  │ PIDIND   │ Q: 79  │ +31%  │ Strong Candidate ││
│  │ NESTLEIND│ Q: 82  │ +8%   │ Candidate        ││
│  └──────────┴────────┴────────┴─────────────────┘│
│                                                    │
│  Click any thesis to view full details and edit.  │
│                                                    │
│  ─────────────────────────────────────────────    │
│                                                    │
│  Postmortems (1)                                  │
│  ┌──────────┬────────┬────────┬─────────────────┐│
│  │ RELIANCE │ +14.3% │ 9 mo  │ Thesis was right ││
│  └──────────┴────────┴────────┴─────────────────┘│
│                                                    │
│  Click any postmortem to review lessons.          │
└──────────────────────────────────────────────────┘
```

### Creating a Postmortem

When you eventually sell a stock, you create a postmortem:

```
┌─────────────────────────────────────────┐
│  📋 POSTMORTEM: RELIANCE.NS             │
│                                         │
│  Entry: 2026-06-15  |  ₹2,800          │
│  Exit:  2027-03-10  |  ₹3,200          │
│  Return: +14.3%                         │
│  Holding period: 9 months               │
│                                         │
│  Why I bought:                          │
│  [Original thesis auto-displayed]       │
│                                         │
│  Why I sold:                            │
│  [You write this]                       │
│                                         │
│  Was my thesis right?                   │
│  [You write this]                       │
│                                         │
│  Key lessons:                           │
│  [You write this]                       │
│                                         │
│  Mistakes made:                         │
│  [You write this]                       │
└─────────────────────────────────────────┘
```

Over years, your postmortem collection becomes the most valuable part of the entire tool.

---

## The Complete User Journey

```
1. RUN SCREENER
   "Show me all quality stocks in Nifty 500"
   → Get ranked table of 500 stocks
   → Focus on Strong Candidates and Candidates
                    ↓

2. ANALYZE TOP PICKS (pick 3-5 stocks)
   Click each → read scorecard → check valuation range
   → review trend charts
   "Is this actually a quality business at a reasonable price?"
                    ↓

3. GOVERNANCE CHECK (manual — you do this yourself)
   Go to Screener.in or read annual reports
   Check promoter pledge, auditor, related-party transactions
   Come back to the app → check the boxes
                    ↓

4. SAVE THESIS
   Write why you're interested
   Write what would prove you wrong
   Write when you'd sell
                    ↓

5. MAKE YOUR DECISION (outside the app)
   The app says "Strong Candidate" — YOU say "Buy" or "Not yet"
   The app is your research analyst, NOT your portfolio manager
                    ↓

6. MONITOR (re-run screener periodically)
   Re-scan every few weeks
   Check if your thesis stocks still score well
   Watch for quality deterioration or price drops
                    ↓

7. POSTMORTEM (when you eventually sell)
   Record what happened and what you learned
   This becomes your most valuable dataset over time
```

---

## What Happens at Each Layer

| What you see | Browser | Python backend | Internet |
|---|---|---|---|
| Click "Run Scan" | Sends `POST /api/screen` to localhost | Loops through 500 tickers, calculates scores | yfinance fetches from Yahoo Finance |
| Quality Score table | Renders HTML table from JSON response | Runs 11 criteria checks, sums weighted score | Nothing — math is local |
| Valuation range | Renders intrinsic value bars | Calculates Graham #, DCF, Earnings Yield | Nothing — math is local |
| Check governance box | Sends checkbox state to backend | Saves to JSON file on disk | Nothing — stored locally |
| Save thesis | Sends `POST /api/thesis` | Writes JSON to `data/theses/` folder | Nothing — stored locally |
| View thesis board | Sends `GET /api/theses` | Reads JSON files from disk | Nothing — reads locally |

---

## What Is and Isn't Automated

| Step | Automated? | How |
|---|---|---|
| Fetching stock list | ✅ Yes | nselib → NSE website |
| Fetching financials | ✅ Yes | yfinance → Yahoo Finance |
| Quality Score calculation | ✅ Yes | Python arithmetic |
| Valuation calculations | ✅ Yes | Python arithmetic |
| Conviction label | ✅ Yes | Python if-else logic |
| Governance check | ❌ No | You read annual reports and check boxes |
| Thesis writing | ❌ No | You write your own reasoning |
| Buy/Sell decision | ❌ No | You decide — the app is your analyst, not your manager |
| Postmortem | ❌ No | You reflect and write lessons |

---

## Financial Sector Handling

When a financial sector stock appears (banks, NBFCs, insurers):

```
┌──────────────────────────────────────────────────┐
│  ⚠️ HDFCBANK.NS — Financial Sector               │
│                                                    │
│  Standard screening criteria (D/E, current ratio, │
│  operating margins) do not apply to banks/NBFCs.  │
│                                                    │
│  Sector-specific analysis (P/B, NPA ratio, NIM,   │
│  CASA ratio) is planned for Phase 2.              │
│                                                    │
│  Quality Score: Not calculated                    │
│  Valuation: Not calculated                        │
│                                                    │
│  You can still save a thesis for this stock.      │
└──────────────────────────────────────────────────┘
```

No fake scores for stocks where the criteria don't apply.

---

## Data Disclaimer

Shown on every analysis page:

> ⚠️ **Financial history limited to ~4 years (yfinance).** This is insufficient for full Graham-style 10-year analysis. Cross-check against Screener.in or annual reports for longer history. Phase 2 will add 10-year data support.

---

## Summary

| Question | Answer |
|---|---|
| Is AI/LLM involved? | **No.** Zero AI. Pure data + math. |
| Is it free? | **Yes.** 100% free. No API keys. No subscriptions. |
| Does it need internet? | **Only** to fetch stock data. Analysis runs offline. |
| Where does it run? | Locally on your PC at localhost:8000. |
| Where is data stored? | JSON files in the `data/` folder on your PC. |
| Can it run automatically? | The screener can be triggered manually. Scheduled auto-runs planned for Phase 3. |
| What's the catch? | yfinance is unofficial (can break). Data limited to ~4 years. Rate limited (~1 request/second). |
| Does it tell me what to buy? | **No.** It tells you "Strong Candidate" — YOU decide whether to buy. |
