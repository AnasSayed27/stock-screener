# Discovery Lens: Category A Structural Domain Fixes & Guardrails

**Date:** November 15, 2026  
**Implementation Scope:** Category A Structural Fixes (Zero Overfitting Risk)  
**Modules Modified:**
- `backend/discovery_prompts.py`
- `backend/discovery_tools.py`

---

## 1. Executive Summary & Rationale

Empirical evaluation of the July 27, 2026 Master Synthesis and Discovery history revealed a stark divergence:
1. **Long-Term Multi-Quarter Theses:** Evaluating high-growth compounders (`AZAD`, `PTCIL`) over 110 days during a mild index dip (-5.24% Nifty) is vulnerable to short-term multiple compression. Hard-capping multiples or re-weighting lenses at this stage would be classic quantitative overfitting.
2. **Structural Domain Bugs:** Conversely, failures in commodity cyclical plays (`JKPAPER`, `SESHAPAPER`, `AMBIKCO`), regulatory demergers (`GUJGASLTD`), and spot tanker rates (`GEESHIP`) were caused by missing fundamental domain rules in corporate law, international trade policy, and cyclical commodity pricing.

**Decision:** Deploy permanent domain guardrails immediately (Category A), while freezing valuation caps and lens re-weighting for 8–12 months until 4–6 quarters of earnings are available.

---

## 2. Detailed Upgrades Deployed

### A. Capital Cycle: Import-Dumping & Vertical Integration Gate
- **File:** `backend/discovery_prompts.py` (`capital_cycle` strategy)
- **Problem Addressed:** Domestic competitor capacity closures do not create pricing power if zero-duty foreign imports (e.g., Chinese or ASEAN dumping under FTAs) flood the market (`JKPAPER` -23.77%, `SESHAPAPER` -17.14%, `AMBIKCO` -23.72%). In contrast, `KPRMILL` (+5.14%) survived because 40%+ captive green power and vertical garmenting shielded margins.
- **Guardrail Added:**
  - Mandatory check for active tariff protection (anti-dumping duties, countervailing duties, ALMM, BIS certification).
  - Standalone single-stage commodity processors without tariff shielding are rejected unless they possess $\ge 35\%$ captive power/raw materials AND downstream value-added forward integration.

### B. Special Situations: Indian Statutory Timeline & Authority Gate
- **File:** `backend/discovery_prompts.py` (`corporate_restructuring` strategy)
- **Problem Addressed:** The engine anticipated a 30–90 day forced-selling window for `GUJGASLTD` (-33.35%). Under Indian corporate jurisprudence, composite schemes and demergers require sequential approvals across NCLT benches, MCA, SEBI/exchanges, and creditor consortia, taking 12 to 24 months.
- **Guardrail Added:**
  - Explicit bifurcation into:
    - **Class A (Rule-Bound / Fast):** SEBI special call auctions for holding companies, tender-offer buybacks (0–3 months).
    - **Class B (Multi-Agency Court Demergers):** Mandatory 12–24 month timeline assumption. Demergers at the pre-NCLT or court stage cannot be labeled near-term catalysts (0–6m) until the final NCLT order is sealed and the formal Record Date is gazetted.

### C. Master Synthesis: Contrarian Spot-Commodity & Peak-Cycle Risk Penalty
- **File:** `backend/discovery_prompts.py` (`MASTER_SYNTHESIS_PROMPT`)
- **Problem Addressed:** The synthesis engine accurately predicted spot tanker rate collapse for `GEESHIP` and gas margin compression for `GUJGASLTD`, but ranked them #3 and #7 anyway.
- **Guardrail Added:**
  - Automated rule requiring the CIO synthesizer to penalize candidates whose theses rely on peak spot commodity rates (e.g. abnormal tanker charter rates), unhedged commodity spreads, or unapproved court demergers.
  - Mandates that peak spot or cyclical commodity plays cannot be ranked above asset-light, net-cash monopolies or mission-critical certified suppliers.

### D. Micro-Cap Liquidity & Float Gate
- **Files:** `backend/discovery_prompts.py` (`SYNTHESIS_SYSTEM_PROMPT`), `backend/discovery_tools.py` (`tool_get_quality_scorecard`)
- **Problem Addressed:** Micro-cap penny stocks (like `543678` Ambo Agritec) distort strategy metrics with thin-float spikes that lack institutional custody or fundamental backing.
- **Guardrail Added:**
  - System prompt constraint rejecting micro-caps with Market Cap $< ₹300\text{ Cr}$ or illiquid float.
  - `tool_get_quality_scorecard` now returns `is_microcap_illiquid` and a `liquidity_warning` flag when market cap is below ₹300 Cr.

---

## 3. Items Explicitly Frozen (Category B)

The following proposed updates are **frozen for 8–12 months** (until after Q4 FY27 / May 2027 earnings):
1. **Hard P/E > 75x Cap on Compounders:** `AZAD` and `PTCIL` executed with blowout earnings growth (+35% to +112% PAT). Multiple compression over 110 days is normal consolidation for high-growth aerospace/defense suppliers.
2. **Re-Weighting Discovery Lenses:** Sample sizes of $N=1$ or $N=2$ are statistically insufficient to alter lens scheduling or priority.
