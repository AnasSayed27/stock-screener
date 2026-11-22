# StockLens Update History

Concise decision & change audit log for future reference, empirical review, and rollback.

---

## UPD-000 — Category A Structural Domain Fixes & Portfolio Guardrails
**Date:** 2026-11-15 | **Status:** `Implemented & Verified` | **Scope:** Prompts, Discovery tools, Synthesis ranking & portfolio guardrails, Valuator credit gates, Benchmark tests

### Before → After
| Dimension | Before | After |
|---|---|---|
| Capital Cycle Gate | Domestic competitor exits assumed to restore pricing power | **Mandatory Tariff / ALMM shield** or $\ge 35\%$ captive power + forward integration (rejects unhedged commodity processors) |
| Special Situations Horizon | Unbounded "30–90 day" forced-selling expectation | **Bifurcated: Class A** (fast rule-bound, 0–3m) vs. **Class B** (court/NCLT schemes, mandatory 12–24m lead time) |
| Contrarian Risk in Synthesis | Text warnings ignored in ranking (#3 `GEESHIP`, #7 `GUJGASLTD`) | **Automated conviction penalty** for peak spot commodity rates or unapproved court demergers |
| Micro-Cap Liquidity Gate | Unfiltered float allowing thin-float penny stock distortions (`543678` +813%) | **Market Cap $\ge ₹300\text{ Cr}$ filter** in prompts + `is_microcap_illiquid` tool flag |
| Multi-Lens Convergence | Uncapped convergence multiplier elevating 100x+ P/E stocks to Rank #1 (`AZAD`) | **Convergence Halving** for P/E $> 75\text{x}$ (`effective = 1 + (conv - 1) / 2`) |
| Portfolio Ecosystem Cap | Uncapped clustering (3 of 7 top picks in CGD/PNGRB = 43% correlated risk) | **Deterministic Ecosystem Cap ($\le 2$ picks)** with auto-demotion to Honorable Mentions |
| Order-Book Quality | Backlog size treated as cash without financing check (`HPL` vs `WABAG`) | **D/E $> 1.2\text{x}$ warning** + **D/E $> 1.5\text{x}$ valuation penalty (-10% MoS)** |
| Evaluation Benchmarking | Small/mid-caps measured exclusively against Nifty 50 (-5.24%), giving fake +1.34% alpha | **Size-tier mapping:** Nifty Smallcap 250 ($<₹25\text{k Cr}$), Nifty Midcap 150 ($₹25\text{k}–₹80\text{k Cr}$) |

### What & Why
- **What:** Deployed 8 zero-overfitting domain guardrails across prompt gates, tool flags, deterministic Python portfolio ranking/capping, credit valuation checks, and size-appropriate benchmark test assertions, while explicitly freezing valuation caps and lens re-weighting for 8–12 months.
- **Why:** The 4-month empirical evaluation (July 27 – Nov 14, 2026) revealed that fundamental thesis selection was strong (62.1% hit rate), but portfolio synthesis suffered from top-heavy conviction inversion (Ranks 1–3 averaged -15.27% vs Ranks 4–6 at +18.25%), single-ecosystem correlation, unhedged FTA dumping traps (`JKPAPER` -23.8%, `AMBIKCO` -23.7%), statutory court delays (`GUJGASLTD` -33.4%), and penny-stock warrant noise (`543678` +813%).

### Exactly How
1. `backend/discovery_prompts.py`: Added mandatory Import-Dumping & Vertical Integration Gate to `capital_cycle`; added Class A vs Class B 12–24m statutory lead-time rule to `corporate_restructuring`; added contrarian spot-commodity / peak-cycle ranking penalties and cash flow discipline to `MASTER_SYNTHESIS_PROMPT`; added `< ₹300 Cr` float constraint to `SYNTHESIS_SYSTEM_PROMPT`.
2. `backend/discovery_tools.py`: Updated `tool_get_quality_scorecard` to calculate `market_cap_cr`, evaluate `< 300 Cr`, and emit `is_microcap_illiquid` + `liquidity_warning`.
3. `backend/synthesis.py`: Implemented deterministic Python post-processor `apply_portfolio_guardrails()`: applies Halving Method (`effective_conv = 1 + (conv - 1) / 2`) on P/E $> 75\text{x}$ stocks; tags regulatory clusters via `ECOSYSTEM_KEYWORDS` (`cgd_pngrb`, `defense_mod`, `smart_meter_rdss`, `railways_mor`) and caps each cluster at $\le 2$ picks in Ultimate Picks, auto-demoting excess candidates to Honorable Mentions.
4. `backend/models.py` & `backend/valuator.py`: Extended `ValuationResult` with `debt_to_equity` and `financing_drag_warning`; checks balance sheet leverage to flag D/E $> 1.2\text{x}$ and penalize Margin of Safety by -10% for D/E $> 1.5\text{x}$.
5. `tests/test_evaluation_report.py`: Added unit test assertions enforcing size-appropriate benchmarking against Nifty Smallcap 250 and Nifty Midcap 150.

### Options Rejected & Why
- **Hard-cap P/E > 75x on compounders today:** Overfitting risk. `AZAD` and `PTCIL` doubled earnings (+35% to +112% PAT) and 110 days is normal multiple consolidation.
- **Re-weight discovery lenses now:** Statistical overfitting on $N=1$ or $N=2$ sample sizes (`hidden_monopoly` $N=2$, `hidden_earnings` $N=1$).
- **Hard-cap multi-lens convergence to 1:** Destroys genuine discovery signal; halving dampens media echo chambers without erasing multi-angle agreement.
- **Prompt-only enforcement of portfolio caps:** LLMs routinely rationalize around soft prompt instructions (as seen when ranking #3 `GEESHIP` and #7 `GUJGASLTD`); portfolio caps require deterministic Python code.
- **Immediate Total Return Index & daily tick Max Drawdown scrapers:** Low ROI over 110 days (`GEESHIP`'s ₹9 dividend added only +0.61%, changing zero conclusions); staged for 1-year review.

### Downgrades & Mitigations
| Actual Downgrade | Mitigation |
|---|---|
| High-conviction 3rd stock in an ecosystem demoted | Retained in Honorable Mentions with transparent portfolio diversification reason. |
| Potential exclusion of low-cost domestic survivor facing dumping | Exemption allowed if company has $\ge 35\%$ captive power + downstream vertical integration (`KPRMILL`). |
| Lower margin of safety for capital-intensive order-book plays | Proportional penalty (-10%) penalizes over-leverage without outright disqualification. |
| Slightly dampened raw score for multi-lens compounders | Retains effective score of 2.5 for 4-count picks, keeping them competitive on quality. |

### Verification & Rollback
- **Tests:** `tests/test_evaluation_report.py` (7/7 pass) + `tests/test_strategy_consolidation.py` (9/9 pass); Python byte-compilation (`py_compile`) clean across all modified files.
- **Git Audit Trail:** Documented in `docs/CATEGORY_A_DOMAIN_FIXES.md`; committed across `b570146`, `2e587ee`, and `71e3ca3`.
- **Rollback Safety:** All additions in `synthesis.py` and `valuator.py` are additive post-processing layers that gracefully handle missing financial fields without crashing.

### Next Review Trigger
- Re-audit at **Q4 FY27 earnings (May/June 2027 — full 10–12 month mark)** with 4–6 quarters of earnings data to evaluate whether Category B frozen items (hard P/E caps, lens re-weighting) should be activated or permanently retired.

---

## UPD-001 — DiscoveryLens Consolidation (11 → 6 Core + Custom Research)
**Date:** 2026-11-21 | **Status:** `Implemented & Verified` | **Scope:** Strategy registry, Evaluator checklists, Synthesis threshold, Discovery UI

### Before → After
| Dimension | Before | After |
|---|---|---|
| Active Strategies | 11 mixed lenses | **6 Core** (`category: "core"`) + **1 Custom** (`freeform`, `category: "custom"`) |
| Kept Pure (Untouched) | 4 lenses | `hidden_monopoly`, `supply_chain`, `capital_cycle`, `corporate_restructuring` |
| Merged (Clean Unified) | 5 overlapping lenses | `government_policy` + `import_substitution` → `policy_import_substitution`<br>`hidden_earnings` + `anomaly_discovery` + filtered `smart_money` → `forensic_anomalies` |
| Retired | `scuttlebutt` | Removed from active runs *(classified Fully Manual in research playbook)* |
| Master Synthesis Min | 7 runs | **5 runs** *(P/E > 75x halving & max-2 ecosystem cap unchanged)* |

### What & Why
- **What:** Consolidated 11 overlapping strategies into 6 orthogonal core lenses, moved `freeform` to a dedicated **Custom Research** UI card, retired `scuttlebutt`, aligned Evaluator checklists to the 7 active IDs, and lowered Master Synthesis minimum to 5.
- **Why:** Cuts full-sweep API/Tavily cost & runtime by **~40–45%**, removes Grade D standalone `smart_money` micro-cap traps and web-unviable `scuttlebutt`, and stops correlated double-counting (`hidden_earnings` + `anomaly_discovery` surfacing the same stock via the same mechanism).

### Exactly How
1. `backend/discovery_prompts.py`: Added `category` (`core`/`custom`); preserved all 4 kept prompts + `freeform` verbatim; cleanly unified the 2 merged prompts (no forced sub-strategy quotas) + NotebookLM safety checks (`CFO/PAT > 0.8x`, `>20%` promoter pledge disqualifier, `<3` analysts neglect context); removed `scuttlebutt`.
2. `backend/discovery_phases.py`: Replaced legacy `STRATEGY_COVERAGE_CHECKLISTS` with exact 7-key checklists (Phase 1 `BREADTH GATE` enforces multi-angle exploration via the stronger Evaluator model).
3. `backend/synthesis.py` & `backend/main.py`: Lowered min discoveries `< 7` → `< 5`; exposed `category` in `/api/discovery/strategies`.
4. `frontend/js/discovery.js`: Filtered main selector to 6 core strategies (default `policy_import_substitution`), added **Custom Research** card (`freeform`) sharing progress/stop state, removed `scuttlebutt` badge, updated UI minimum to `5`, preserved legacy saved-run viewing/synthesis.

### Options Rejected & Why
- **Keep 11 strategies:** Wastes ~40–45% API budget, retains Grade D noise, and inflates convergence via overlap.
- **Cut to 5 (merge `supply_chain` into `hidden_monopoly`):** Risks diluting #1 A+ lens (`hidden_monopoly`) and weakens independent convergence.
- **Cut to 4 (drop `capital_cycle` or `corporate_restructuring`):** Loses genuinely uncorrelated cyclical/event-driven alpha regimes.
- **Forced "Sub-Strategy A / B" quotas inside prompts:** Conflicts with `QUALITY GATE` and causes lightweight worker quota-padding.

### Downgrades & Mitigations
| Actual Downgrade | Mitigation |
|---|---|
| ~35–45% smaller candidate pool per sweep | Kept `supply_chain` & `hidden_monopoly` separate; lowered synthesis min to 5. |
| 3 anomaly types share 1 Phase 1 scan (`forensic_anomalies`) | Stronger Evaluator's Phase 1 checklist audits all 3 angles; optional focus keyword retained. |
| Slight manufacturing tilt in `policy_import_substitution` | Framed around *"policy-created or tariff-protected domestic TAM"* + escrow & tariff checklist items. |
| Coarser lens-level attribution | Per-candidate `connection_type` preserved for exact mechanism tracking. |
| No automated B2C consumer scan (`scuttlebutt` retired) | B2B specifier loyalty remains in `hidden_monopoly`; ad-hoc checks use **Custom Research**. |

### Verification & Rollback
- **Tests:** `tests/test_strategy_consolidation.py` (9/9 pass, verified red→green) + `tests/test_evaluation_report.py` (7/7 pass); `py_compile` & `node --check` clean.
- **Playbook Cross-Check:** Verified unbiasedly against `NoteboolLM_answers.md` (PLI lag, O2B + `CFO/PAT > 0.8x`, Ind AS expensing, customer advances, `>1%` creeping acquisition, `>20%` pledge disqualifier).
- **Backward Compatibility:** Saved JSON runs store strategy IDs as strings — old runs stay readable, synthesizable, and deletable with zero migration.

### Next Review Trigger
- Re-audit after **2 full 6-strategy sweeps + 1 Master Synthesis run**: confirm (a) 5–8 high-conviction picks survive ecosystem caps, and (b) `forensic_anomalies` does not collapse onto a single anomaly subtype.
