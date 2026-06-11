# Personal Investment Strategy

> Fundamental analysis approach for individual retail investors.
> Synthesized from: Graham, Lynch, Fisher, Greenblatt, Buffett, Marks, Klarman, Damodaran.

---

## Core Philosophy

**Quality companies at reasonable prices, with a margin of safety.**

This strategy leans 70% toward buying quality businesses at fair-to-cheap prices (Buffett/Fisher style) and 30% toward deep statistical value (Graham/Greenblatt style). It prioritizes quantitative screening with a qualitative final check.

---

## Strategic Positions (Resolved Disagreements)

| Decision | Chosen Position | Rationale |
|---|---|---|
| **Quant vs. Qual** | 80% Quantitative / 20% Qualitative | Numbers screen first, qualitative as final pass. Automatable and emotion-proof. |
| **Value vs. Growth** | 70% Quality-at-fair-price / 30% Deep Value | Avoids value traps. Greenblatt-style: cheap AND efficient. |
| **Past vs. Future data** | 70% Historical / 30% Forward projections | Use 5-10 year historical averages as base. Only layer in modest future estimates. |
| **Diversification** | 15-20 stocks | Wide enough to absorb mistakes, narrow enough to research properly. |
| **Macro awareness** | 20% weight (3 simple checks) | Recognize obvious extremes only. Don't try to predict cycles. |
| **Debt limits** | Moderate — D/E < 1.0, debt payable within 5 yrs of FCF | Protective without being so strict it eliminates good companies. |
| **Dividends** | Don't require. Prefer reinvestment at high ROIC. | Accept dividends as a bonus, not a filter. |

---

## The Pipeline

```
Step 1: Idea Generation & Initial Screening
          ↓
Step 2: Financial Health & Solvency Check
          ↓
Step 3: Profitability & Capital Efficiency
          ↓
Step 4: Qualitative Assessment (20% weight)
          ↓
Step 5: Valuation & Pricing
          ↓
Step 6: Margin of Safety & Buy Decision
          ↓
Step 7: Portfolio Construction & Monitoring
```

---

## Step 1: Idea Generation & Initial Screening

**Goal:** Narrow 5,000+ stocks → 30-50 candidates using rule-based filters.

### Sources of ideas
- **Circle of Competence:** Only consider industries/businesses you understand (Buffett, Lynch)
- **Everyday observation:** Notice products, trends, companies you interact with (Lynch)
- **Quantitative screens:** Run programmatic screens (Greenblatt, Graham)

### Initial quantitative screen (pass/fail gates)
| Criterion | Threshold | Source |
|---|---|---|
| Market cap | > $500M (avoid micro-caps as beginner) | Practical |
| Sector exclusions | Exclude financials & utilities (different metrics) | Greenblatt |
| Earnings history | Positive earnings in at least 8 of last 10 years | Graham |
| Free cash flow | Positive FCF in at least 4 of last 5 years | Everything Money |

---

## Step 2: Financial Health & Solvency

**Goal:** Eliminate companies at risk of financial distress.

| Criterion | Threshold | Source |
|---|---|---|
| Debt-to-Equity | < 1.0 | Moderate (Graham/Lynch adapted) |
| Long-term debt coverage | Payable within 5 years of avg FCF | Everything Money |
| Current ratio | > 1.5 (ideally > 2.0) | Graham |
| Share dilution | Shares outstanding stable or decreasing over 5 years | Everything Money |

> [!WARNING]
> If a company fails ANY of these, discard it. Financial health is non-negotiable.

---

## Step 3: Profitability & Capital Efficiency

**Goal:** Confirm the company generates strong returns on invested capital.

| Criterion | Threshold | Source |
|---|---|---|
| ROIC (Return on Invested Capital) | > 12% (5-year average) | Buffett, Everything Money |
| ROE (Return on Equity) | > 15% (consistent over 5-10 years) | Buffett |
| Operating margins | Stable or expanding, double-digit preferred | General consensus |
| FCF vs. Net Income | FCF should approximate or exceed net income | Everything Money |
| Earnings Yield (EBIT / EV) | High relative to risk-free rate | Greenblatt |

> [!NOTE]
> High ROIC + low debt = genuinely efficient business. High ROE with high debt = artificial — be cautious.

---

## Step 4: Qualitative Assessment (20% Weight)

**Goal:** Final human check on business quality and management. This step is NOT for screening — it's for validating stocks that already passed Steps 1-3.

### Economic Moat
- Does the business have a durable competitive advantage?
- Types: brand power, scale, network effects, switching costs, patents
- Source: Buffett, Fisher

### Management Quality
- Do they admit mistakes candidly in annual reports? (Buffett)
- Do they allocate capital rationally — buybacks when cheap, no overpriced acquisitions? (Fisher, Buffett)
- Are insiders buying stock with their own money? (Lynch)

### Business Story
- Classify the stock: fast grower, stalwart, slow grower, cyclical, turnaround, asset play (Lynch)
- Does the qualitative story match the financial numbers? (Damodaran)

### Red Flags (auto-discard)
- Management compensation growing faster than earnings
- Frequent acquisitions with no clear strategic logic
- Accounting restatements or auditor changes
- Revenue growing but FCF declining

---

## Step 5: Valuation & Pricing

**Goal:** Determine intrinsic value. Use multiple methods and triangulate.

### Primary methods (70% weight — historical)
| Method | Formula | When to use | Source |
|---|---|---|---|
| Graham Number | √(22.5 × EPS × Book Value per Share) | Stable, mature companies | Graham |
| Earnings Yield | EBIT / Enterprise Value | Comparing across companies | Greenblatt |
| PEG Ratio | P/E ÷ Earnings Growth Rate (PEG ≤ 1.0 = cheap) | Growth companies | Lynch |
| Relative multiples | EV/EBITDA, P/E vs. industry peers | All — context-dependent | Damodaran |

### Secondary method (30% weight — forward)
| Method | Formula | Notes | Source |
|---|---|---|---|
| Simple DCF | Present value of projected FCF over 10 years | Use conservative growth assumptions. Use historical avg FCF as base. Apply a 10% discount rate. | Buffett, Damodaran |

### Triangulation (Klarman's approach)
- Calculate intrinsic value using at least 2 methods
- Take the **lower** estimate as your working intrinsic value
- This builds conservatism into the process

---

## Step 6: Margin of Safety & Buy Decision

**Goal:** Only buy if the price is significantly below intrinsic value.

### Margin of Safety
| Rule | Threshold | Source |
|---|---|---|
| Minimum discount to intrinsic value | **25-30%** below calculated intrinsic value | Graham, Buffett, Klarman |
| Higher margin for uncertain companies | **40-50%** for companies with less predictable earnings | Klarman |

### Second-Level Thinking Check (Marks)
Before buying, ask:
- ❓ Is the consensus too optimistic about this stock? → Don't buy popular stocks at full price
- ❓ Is the consensus too pessimistic? → This is where bargains come from
- ❓ What could go wrong that I haven't considered?

### Macro Check (20% weight — 3 simple indicators)
| Check | What it tells you | Action |
|---|---|---|
| Market-wide Shiller P/E | Is the overall market expensive or cheap? | If extremely high (>30), be more selective. If low (<15), be more aggressive. |
| Interest rate direction | Is money getting cheaper or more expensive? | Rising rates = headwind for stocks, demand larger margin of safety. |
| Personal cash level | How much dry powder do you have? | In euphoria, hold 20-30% cash. In panic, deploy cash aggressively. |

> [!IMPORTANT]
> Don't try to TIME the market with these. Use them only to CALIBRATE how strict your margin of safety should be.

---

## Step 7: Portfolio Construction & Monitoring

### Portfolio Rules
| Rule | Specification |
|---|---|
| Number of holdings | 15-20 stocks |
| Max position size | 5-7% per stock (equal-weight as default) |
| Sector concentration | No more than 25% in any single sector |
| Cash reserve | 10-20% (adjust based on macro check) |
| Rebalance frequency | Quarterly review |

### Sell Criteria (when to exit)
| Trigger | Action | Source |
|---|---|---|
| Thesis broken | Sell — fundamentals deteriorated beyond recovery | All |
| Overvaluation | Trim or sell if price exceeds intrinsic value by 20%+ | Graham, Marks |
| Better opportunity | Swap for a stock with higher margin of safety | Klarman |
| Reached fair value | Trim position, let remainder run | Lynch |

### What is NOT a sell trigger
- Short-term price decline (if thesis intact)
- Market-wide panic (if thesis intact)
- One bad quarter (if long-term trend intact)

---

## Common Mistakes to Avoid

| Mistake | How to avoid it |
|---|---|
| **Speculating while thinking you're investing** | Stick to the checklist. If a stock doesn't pass the screens, don't buy it regardless of hype. |
| **Extrapolating recent trends** | Don't assume a company that grew 30% last year will grow 30% forever. Use conservative estimates. |
| **Overpaying for quality** | Even great companies can be bad investments at the wrong price. Always demand margin of safety. |
| **Emotional capitulation** | Commit to the strategy for 3-5 years minimum. Expect underperformance in some periods. |
| **Analysis paralysis** | Set a deadline for research. A good-enough strategy executed is better than a perfect strategy never started. |
| **Ignoring value traps** | High ROIC requirement filters out "cheap for a reason" companies. Trust the screen. |

---

## Quick-Reference: Stock Evaluation Checklist

```
□ Step 1: Do I understand this business?
□ Step 1: Has it been profitable 8+ of last 10 years?
□ Step 1: Positive FCF 4+ of last 5 years?

□ Step 2: Debt-to-Equity < 1.0?
□ Step 2: Debt payable within 5 years of avg FCF?
□ Step 2: Current ratio > 1.5?
□ Step 2: No significant share dilution?

□ Step 3: ROIC > 12% (5-year avg)?
□ Step 3: ROE > 15% (consistent)?
□ Step 3: FCF ≈ Net Income?
□ Step 3: High earnings yield?

□ Step 4: Durable competitive moat?
□ Step 4: Honest, capable management?
□ Step 4: Insiders buying?
□ Step 4: No red flags?

□ Step 5: Calculated intrinsic value using 2+ methods?
□ Step 5: Took the lower estimate?

□ Step 6: Price at least 25-30% below intrinsic value?
□ Step 6: Consensus is pessimistic (not euphoric)?
□ Step 6: Macro check — no extreme overvaluation in market?

□ Step 7: Position size ≤ 5-7%?
□ Step 7: Total portfolio ≤ 20 stocks?
□ Step 7: Sector not over 25%?
```

---

## What's Next

This strategy document is the **blueprint**. The next phase is to build an automation tool that executes Steps 1-3 and parts of Step 5 programmatically, presenting you with pre-screened candidates for your qualitative review (Step 4) and final decision (Step 6).
