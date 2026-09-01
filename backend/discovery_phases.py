# -*- coding: utf-8 -*-
"""
DiscoveryLens prompt templates for the 5-Phase Deep Research Pipeline.
"""

THINK_FIRST_PROTOCOL_EXPLORE = """THINK-FIRST PROTOCOL (EXPLORATION):
1. REASON FIRST: Before using the search tool, map out potential sub-sectors, value chain layers, and alternative angles from your training knowledge.
2. DISCOVER BROADLY: Use search to discover real-world sub-sectors, market dynamics, and player types that extend beyond your initial knowledge. Do NOT limit searches to confirming a single idea.
3. REASON OVER RESULTS: After each search, analyze what the result reveals about the wider landscape, second-order implications, and adjacent segments.
4. ANTI-TUNNELING: Keep searches diverse across multiple sub-sectors. Do not spend multiple searches digging deep into one company or single niche early on.
"""

THINK_FIRST_PROTOCOL_VERIFY = """THINK-FIRST PROTOCOL (VERIFICATION & ANALYSIS):
1. REASON FIRST: Before using the search tool, write down what you already know about this topic from your training knowledge. Form hypotheses and identify specific gaps.
2. SEARCH STRATEGICALLY: Only search to verify your hypotheses, find current data your training doesn't cover, or discover information you specifically identified as missing.
3. REASON OVER RESULTS: After each search, don't summarize — analyze what the result means, what new connections it reveals, and what it disproves. Think about second and third-order implications.
4. NEVER search for something you can reason about. Use searches for facts, data, current events, and verification — not for reasoning.
"""

THINK_FIRST_PROTOCOL = THINK_FIRST_PROTOCOL_VERIFY

PHASE_1_LANDSCAPE_PROMPT = THINK_FIRST_PROTOCOL_EXPLORE + """
PHASE 1: LANDSCAPE SCAN
OBJECTIVE: {strategy_objective}

BREADTH-FIRST SEARCH PROTOCOL (Mandatory Execution Stages):

STAGE A — DIVERGENT MAPPING (Searches 1 to 8):
1. Your first 8 searches MUST each target a DIFFERENT sub-sector, value chain layer, or market angle related to the theme.
2. A search counts as "different" ONLY if it targets a segment or angle not covered in your previous searches (e.g. search 1: raw material suppliers, search 2: testing/certification, search 3: equipment providers, search 4: export markets, etc.).
3. FORBIDDEN: Do NOT deep-dive into any single company or perform 2+ consecutive searches on the same sub-sector during Stage A.
4. List all discovered sub-sectors and angles before proceeding to Stage B.

STAGE B — HYPOTHESIS FORMATION (Searches 9 to 11):
1. Based on Stage A, identify exactly 2 to 3 independent, parallel hypotheses (e.g. Hypothesis A: Sub-sector X direct suppliers, Hypothesis B: Sub-sector Y equipment providers, Hypothesis C: Sub-sector Z pick-and-shovel providers).
2. Each hypothesis MUST represent a DIFFERENT sub-sector discovered in Stage A.
3. Assign an initial confidence score (0-100%) and identify candidate companies for each hypothesis.

STAGE C — TARGETED GAP FILL (Searches 12 to {max_iterations}):
1. Use remaining searches to address specific gaps across all 2-3 hypotheses.
2. Do NOT deep-dive into individual company balance sheets yet (that is Phase 3's job).

ANTI-TUNNELING CHECK:
Before every search, check your search history. If 2 or more of your last 3 searches covered the same company or sub-sector, you MUST pivot your next search to a completely different angle.

OUTPUT FORMAT:
Provide a plain-text markdown summary containing:
- **Discovered Landscape & Angles**: List at least 4 distinct sub-sectors/angles explored.
- **Active Hypotheses**: Describe 2-3 parallel hypotheses from different sub-sectors.
- **Initial Confidence**: Confidence score (0-100%) for each.
- **Coverage Assessment**: Areas checked vs. remaining gaps.
- **Key Evidence & Leads**: Initial findings and company leads across all hypotheses.
"""

PHASE_2_CORRECTION_PROMPT = THINK_FIRST_PROTOCOL_VERIFY + """
PHASE 2: COURSE CORRECTION
OBJECTIVE: {strategy_objective}

INPUT EVIDENCE (PHASE 1 SUMMARY):
{phase1_evidence}

INSTRUCTIONS:
1. STEP 0 — PREDICTIVE SCAN (Do this BEFORE challenging Phase 1 assumptions):
   Review Phase 1 candidates. Are they companies that have already received orders, approvals, or major analyst coverage for this exact thesis?
   If YES (lagging-indicator bias), immediately run your first 2 searches specifically to find:
   (a) Pre-event companies in the same space (positioned with capacity/certifications, but confirming order not yet announced).
   (b) Alternative sub-sectors in the same theme that Phase 1 failed to explore.

2. Challenge Phase 1 Assumptions: Act as a devil's advocate. What if the main assumptions in Phase 1 are wrong? What risks were ignored?
3. Actively search for disconfirming evidence or counter-arguments for each active hypothesis.
4. Unused Lenses: Think about alternative angles. If another analyst disagreed with your Phase 1 summary, what would they look for? Search for these aspects.
5. Update Hypotheses: Do NOT eliminate hypotheses yet, but adjust their descriptions and confidence scores based on new findings.
6. Dynamic Budget: You have an iteration budget of up to {max_iterations} searches. Stop early if you have thoroughly challenged the assumptions.

OUTPUT FORMAT:
Provide a plain-text markdown summary containing:
- **Predictive Scan Findings**: Pre-event alternatives and overlooked sub-sectors identified.
- **Assumptions Challenged**: The assumptions analyzed and what you found.
- **Hypothesis Refinements**: Revised hypotheses and updated confidence levels (0-100%).
- **Disconfirming Evidence**: Details of any negative arguments or counter-evidence found.
"""

PHASE_3_DEEPDIVE_PROMPT = THINK_FIRST_PROTOCOL_VERIFY + """
PHASE 3: CANDIDATE DEEP DIVE
OBJECTIVE: {strategy_objective}

INPUT EVIDENCE (PHASE 1 & 2 SUMMARY):
{evidence}

INSTRUCTIONS:
1. Deep-Dive Candidates: For the surviving hypotheses, identify the most promising listed companies in India.
2. Conduct detailed research on each candidate company. Focus on:
   - Recent quarterly financials (revenue growth, margins, debt).
   - Order book, capacity expansion plans, or execution pipelines.
   - Competitive advantages (moats, market share, sole supplier status).
   - Promoter pledge levels and capital allocation track record.
3. Hypothesis Elimination: If a hypothesis is clearly disproved or lacks listed candidates in India, eliminate it and document the reason.
4. Dynamic Budget: You have an iteration budget of up to {max_iterations} searches. Spend it to dig deep into specific company statements and filings.

TOOL USAGE PROTOCOL (Phase 3):
For each promising candidate company identified from Phase 1 & 2 evidence:
  Step 1: Call resolve_ticker(company_name) to get the verified NSE/BSE ticker.
  Step 2: If a valid ticker is returned, call get_stock_financials(ticker) to fetch 4-year audited financial data.
  Step 3: Call get_quality_scorecard(ticker) to compute the fundamental quality score and intrinsic valuations.
Use these audited tool results as your PRIMARY evidence for financials, margins, debt, and valuations — they are more reliable than web search snippets. Continue using search_web for non-financial information (order book, competitive position, management commentary, news).

OUTPUT FORMAT:
Provide a plain-text markdown summary containing:
- **Surviving Hypotheses & Candidates**: High-conviction companies list.
- **Eliminated Hypotheses**: Any directions discarded and why.
- **Company Deep-Dive Dossier**: Financials, order book details, expansion plans, and intermediate confidence scores for each candidate.
"""

PHASE_4_VERIFICATION_PROMPT = THINK_FIRST_PROTOCOL_VERIFY + """
PHASE 4: CROSS-VERIFICATION
OBJECTIVE: {strategy_objective}

INPUT EVIDENCE (PHASES 1-3 SUMMARY):
{evidence}

INSTRUCTIONS:
1. Fact-Check Claims: Verify company names, tickers, listed status (NSE/BSE), and business segments.
2. Search for Red Flags: Look for corporate governance issues, auditor resignations, tax disputes, pledge increases, or negative news.
3. Verify Connections: Cross-check the link between the trend/policy and the candidate company. Is the connection actual/verifiable, or speculative?
4. Dynamic Budget: You have an iteration budget of up to {max_iterations} searches. Use it to double-check details and search for warning signs.

OUTPUT FORMAT:
Provide a plain-text markdown summary containing:
- **Verified Facts**: Confirmed listed status, tickers, and connection links.
- **Red Flags & Disconfirming Evidence**: Any negatives found.
- **Final Pre-Synthesis Confidence**: The updated confidence scores (0-100%) for each candidate.
"""

PHASE_5_SYNTHESIS_PROMPT = """
PHASE 5: SYNTHESIS & SELF-CRITIQUE (NO TOOL CALLS ALLOWED)
OBJECTIVE: {strategy_objective}

ALL ACCUMULATED EVIDENCE:
{all_evidence}

INSTRUCTIONS:
1. You do NOT have access to any search tools in this phase. Perform pure synthesis and logical deduction over the accumulated evidence.
2. AUDITED DATA PRIORITY: If the evidence below includes an "AUDITED CANDIDATE LEDGER" section, treat those numbers as ground truth. When the ledger's audited financials, quality score, or valuation data conflict with earlier web-search estimates from Phases 1-4, ALWAYS use the audited ledger values. The ledger was computed from verified financial statements, not web snippets.
3. Filter Candidates: Apply the **MISPRICING GATE** to each candidate:
   - Identify the **Market Mispricing Type**:
     - TYPE A (WRONG CONSENSUS): State the wrong consensus in one sentence as: "The market currently assumes X, but evidence shows Y."
     - TYPE B (INVISIBLE TO MARKET): State why it is invisible and what trigger forces recognition: "This company is invisible because [reason]. The market will notice it when [trigger]."
     If you cannot state either Type A or Type B clearly, REMOVE the candidate.
   - Evaluate **Thesis Incorporation**: Has this specific thesis — not the company generally — already been widely recognized and incorporated into consensus (sell-side reports, active institutional positioning, forward EPS/revenue estimates)? If YES, downgrade confidence. If it is fully priced in, REMOVE the candidate.
   - Assess the **Recognition Stage**: Label each candidate with its stage (Stage 0: Market is unaware/wrong assumption active; Stage 1: Market is aware but underestimating magnitude/duration; Stage 2: Market understands but hasn't fully priced in; Stage 3: Priced in). Stage 0 and 1 are preferred; Stage 3 = REMOVE candidate.
4. Confidence Evolution: For each candidate, document the history of confidence scores across the phases (Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Final).
5. Self-Critique: Provide a candidate-specific rebuttal answering: "Why might this specific hypothesis be wrong? What would disprove it?"

OUTPUT FORMAT CONSTRAINTS:
You must output a single, valid JSON object matching the requested schema. Do NOT wrap the JSON in Markdown backticks (like ```json ... ```) in your raw output.
The JSON object must match the DiscoveryResult schema:
- **analysis_summary**: Detailed summary synthesizing the final findings.
- **candidates**: A list of candidates, each with:
  - company_name: Name of the company.
  - ticker: NSE/BSE ticker (or null if unsure).
  - connection_type: The role of this company in the thesis.
  - confidence: high | medium | low.
  - why_now: Why THIS moment? What has changed? Must include: (a) what changed, (b) estimated catalyst window (near-term: 0-6 months | medium-term: 6-18 months | long-term: 18+ months) with a brief reason, and (c) confirming milestone (observable event verifying the thesis).
  - reasoning: The complete reasoning chain. Must start with the TYPE A or TYPE B statement, followed by evidence classified into: [OBSERVED FACTS], [STRONG INFERENCE], and [HYPOTHESIS].
  - self_critique: Candidate-specific Rebuttal.
  - disproving_evidence: Specific event/metric that would invalidate this hypothesis.
  - risks: List of specific risks for this company.
  - what_to_verify: List of items to verify. The first item MUST be: 'KILLER ASSUMPTION: [the single critical assumption that, if wrong, invalidates the entire thesis]'.
  - sources: List of source URLs used to back up this candidate.
  - confidence_evolution: List of phase-by-phase confidence scores (e.g., ["Phase 1: 70%", "Phase 2: 50%", "Phase 3: 85%", "Phase 4: 82%"]).
- **limitations**: Overall limits of this analysis.
- **searches_performed**: Do not modify this (this is handled by the wrapper).
- **disclaimer**: Warning disclaimer.
"""

DEPTH_LOOP_CONTINUATION_PROMPT = """
DEPTH LOOP: CONTINUATION (Iteration {loop_iteration} of {max_loops})
OBJECTIVE: {strategy_objective}

PREVIOUS PHASE OUTPUT:
{previous_output}

EVALUATOR ASSESSMENT:
- Coverage Score: {coverage_score}/100
- Reasoning Depth Score: {reasoning_score}/100
- Alternative Analyst Angle: {alternative_angle}

UNCOVERED GAPS (You MUST address these):
{gaps}

MANDATORY SEARCH QUERIES (Execute each of these):
{search_queries}

REASONING TASKS (Think about these WITHOUT searching):
{reasoning_prompts}

SEARCHES ALREADY PERFORMED (Do NOT repeat — avoid searches covering the same intent,
even if phrased differently. e.g., 'PLI beneficiaries', 'PLI scheme beneficiaries', and
'Government incentive beneficiaries' are the same intent — do not re-search them):
{already_searched}

INSTRUCTIONS:
1. Address EVERY gap listed above. Do not skip any.
2. Execute the mandatory search queries first.
3. Then work through the reasoning tasks using your own knowledge.
4. Merge your new findings with the previous output into a comprehensive updated summary.
5. You have an iteration budget of up to {max_iterations} searches for this continuation.

OUTPUT FORMAT:
Provide an UPDATED, MERGED version of the full phase summary incorporating all new findings.
"""

EVALUATOR_PROMPT = """
You are a research quality evaluator for an Indian equity research pipeline. Your job is to
assess whether a research phase has achieved sufficient depth and coverage.

STRATEGY BEING EVALUATED: {strategy_name}
PHASE BEING EVALUATED: {phase_name} (Phase {phase_number}/4)

STRATEGY-SPECIFIC COVERAGE CHECKLIST:
{coverage_checklist}

PHASE OUTPUT TO EVALUATE:
{phase_output}

SEARCHES PERFORMED IN THIS PHASE: {search_count}

PHASE-SCOPED EVALUATION MANDATE:
Only score checklist items relevant to the current phase's purpose. Do NOT penalize a later phase for items that belong to an earlier phase:
- Phase 1: Score ALL checklist items (with emphasis on broad coverage across multiple sub-sectors).
- Phase 2: Score only items related to counter-arguments, risks, alternative angles, and pre-event positioning.
- Phase 3: Score only items related to company-level depth (financials, order book, moats, capacity, promoter data).
- Phase 4: Score only items related to verification (listed status, tickers, red flags, connection validity). Do not flag missing TAM or landscape data as gaps.

EVALUATION CRITERIA:
1. COVERAGE COMPLETENESS (0-100): Has every relevant item in the checklist for this phase been addressed with specific information?
2. REASONING DEPTH (0-100): Did the output demonstrate original reasoning and connections, or just summarize search results? Look for hypothesis formation, causal chains, and second-order thinking.
3. EVIDENCE SPECIFICITY: Are claims backed by specific data (company names, numbers, dates, revenue figures) or vague generalizations?
4. ALTERNATIVE ANALYST ANGLE: Would an experienced analyst with a different mental model likely investigate a substantially different angle that this output has not explored? If yes, describe that angle.
5. GAPS: What specific topics from the checklist remain uncovered or weakly covered?
6. DIMINISHING RETURNS — for each gap, classify its information availability:
   - EASY: Publicly available, findable in 1-2 searches.
   - MEDIUM: Available but requires specific queries or niche sources.
   - HARD: Very sparse online; would require industry contacts or primary research.
   - UNAVAILABLE: Requires insider knowledge, field visits, or non-public data.
    Only include gaps classified EASY or MEDIUM in search_queries.
    Gaps classified HARD or UNAVAILABLE should appear only in reasoning_prompts (reason about them using existing knowledge; do not search).
7. MARKET MISPRICING COVERAGE: Has the output explicitly identified either (a) what consensus assumption the market is currently getting wrong for each candidate (Type A), or (b) why the company is invisible to the market and what trigger will force recognition (Type B)? If this classification is missing or vague, treat it as a high-value gap.
8. BREADTH GATE (Phase 1 Only): If evaluating Phase 1, verify that the output covers a minimum of 4 genuinely distinct sub-sectors or angles. If fewer than 4 distinct sub-sectors/angles are present, set should_continue=TRUE and add a breadth gap ("Fewer than 4 distinct sub-sectors explored in Phase 1 landscape scan") regardless of other coverage scores.

TERMINATION DECISION — `should_continue`:
  Set to TRUE only if ALL of the following hold:
  - At least one HIGH-VALUE gap remains (checklist item, alternative analyst angle, or Phase 1 breadth failure)
  - AND at least one such gap is classified EASY or MEDIUM (i.e., searchable)
  - AND you genuinely believe another loop would produce meaningfully different insights
  Set to FALSE if:
  - All remaining gaps are HARD or UNAVAILABLE, OR
  - No meaningful gap remains regardless of scores, OR
  - Additional loops would only produce marginal or repetitive information
  Do NOT set to TRUE just because scores are below a number.
  Do NOT set to FALSE just because scores are above a number.
  The scores are signals — your judgment is the final decision.

OUTPUT (JSON):
{{
  "coverage_score": 0,
  "reasoning_depth_score": 0,
  "alternative_analyst_angle": null,
  "gaps": [
    {{"topic": "<gap description>", "availability": "EASY|MEDIUM|HARD|UNAVAILABLE"}}
  ],
  "search_queries": ["<specific query for EASY/MEDIUM gaps only>"],
  "reasoning_prompts": ["<question to reason about for HARD/UNAVAILABLE gaps>"],
  "should_continue": false,
  "termination_reason": "<brief explanation of why you set should_continue as you did>"
}}
"""

STRATEGY_COVERAGE_CHECKLISTS = {
    "government_policy": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct sub-sectors, value chain layers, or policy impact areas were explored and named
    - [ ] Policy mechanism details (what is mandated/funded/incentivized)
    - [ ] Total Addressable Market (TAM) with specific numbers
    - [ ] Direct beneficiary companies (with names)
    - [ ] Supply chain mapping (raw material → component → equipment → service providers)
    - [ ] Second/third-order beneficiaries
    - [ ] Funding mechanism (escrow vs annual budget)
    - [ ] Timeline and implementation status
    - [ ] Competitive landscape among beneficiaries
    - [ ] Failure modes and policy reversal risks
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "supply_chain": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct sub-sectors, value chain layers, or supplier categories were explored and named
    - [ ] End-product/sector boom validation with data
    - [ ] Complete backward value chain map (raw materials → components → equipment → services)
    - [ ] Chokepoint identification (non-substitutable inputs)
    - [ ] Payment hierarchy (who gets paid first)
    - [ ] Listed supplier companies (with names)
    - [ ] Capacity constraints and pricing power analysis
    - [ ] Customer concentration risk
    - [ ] Alternative suppliers and substitution risk
    - [ ] Cyclicality risk of the end-product boom
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "hidden_monopoly": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct niche segments or monopoly candidate areas were explored and named
    - [ ] Niche segment identification with market size
    - [ ] Monopoly/duopoly company names
    - [ ] Toll-road characteristics verified (low cost share, high failure cost, high switching cost)
    - [ ] Entry barrier analysis (certifications, IP, years to replicate)
    - [ ] Pricing power evidence
    - [ ] Demand captivity (recession-proof?)
    - [ ] Technology disruption risk
    - [ ] Customer concentration
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "import_substitution": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct import categories or sub-sectors were explored and named
    - [ ] Import bill size with specific numbers
    - [ ] Current domestic manufacturing percentage
    - [ ] Government targets for domestic production
    - [ ] Tariff/anti-dumping protection details
    - [ ] Domestic manufacturer companies (with names)
    - [ ] Cost competitiveness without subsidies
    - [ ] Quality parity with imports
    - [ ] PLI scheme details and approval status
    - [ ] Capacity expansion timelines
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "capital_cycle": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct distressed industries or cyclical sub-sectors were explored and named
    - [ ] Sector distress validation (stock crashes, losses, frozen capex)
    - [ ] Capital cycle stage assessment
    - [ ] Competitor exits/shutdowns (with names)
    - [ ] Survivor company identification (profitable, low debt)
    - [ ] Operating leverage calculation potential
    - [ ] Cycle turn triggers
    - [ ] Insider buying signals
    - [ ] Duration risk (how long can survivor survive)
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "hidden_earnings": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct earnings suppression mechanisms or company types were explored and named
    - [ ] Companies with CFO > PAT divergence identified
    - [ ] Specific suppressing line items (depreciation, R&D expensing, write-offs)
    - [ ] Capex cycle timeline (when does it peak?)
    - [ ] Normalized margin projection
    - [ ] Cash flow quality verification
    - [ ] Comparison with competitor accounting policies
    - [ ] Working capital manipulation check
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "corporate_restructuring": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct restructuring types or demerger categories were explored and named
    - [ ] Recent demergers/spinoffs/NCLT exits identified
    - [ ] Institutional forced selling evidence
    - [ ] Insider behavior in demerged entity (promoter stake changes)
    - [ ] Standalone business quality of new entity
    - [ ] Sum-of-parts valuation
    - [ ] Analyst coverage vacuum confirmation
    - [ ] Regulatory/legal risks to the restructuring
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "scuttlebutt": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct consumer trends or product categories were explored and named
    - [ ] Trending product/brand identification with evidence
    - [ ] Manufacturer/parent company traced (listed status confirmed)
    - [ ] Product-market fit indicators (repeat purchase, word-of-mouth, professional recommendation)
    - [ ] Competitive moat assessment
    - [ ] Distribution channel analysis
    - [ ] Scalability of production
    - [ ] Fad vs trend distinction
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "smart_money": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct promoter buying clusters or insider accumulation sectors were explored and named
    - [ ] Promoter buying events identified (with dates, volumes)
    - [ ] Purchase price vs market price analysis (premium buying?)
    - [ ] Consistency check (2+ quarters of buying)
    - [ ] Catalyst investigation (why are insiders buying?)
    - [ ] Analyst coverage check (zero coverage = higher signal)
    - [ ] Institutional holding levels
    - [ ] Related-party transaction screening
    - [ ] Promoter track record (past buying → stock performance)
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "anomaly_discovery": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct financial/operational anomaly patterns were explored and named
    - [ ] Anomaly identified with specific data points
    - [ ] Contradiction reconciled (why does this exist?)
    - [ ] Underlying business quality assessed
    - [ ] Inflection point/catalyst defined
    - [ ] Fraud/manipulation ruled out or flagged
    - [ ] Comparable anomalies in other companies
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """,
    "freeform": """
    - [ ] BREADTH GATE (Phase 1): At least 4 distinct sub-sectors, angles, or value chain perspectives were explored and named
    - [ ] Core question/hypothesis understood and stated
    - [ ] Multiple angles researched (not just one direction)
    - [ ] Listed companies mapped to the hypothesis
    - [ ] Second-order effects explored
    - [ ] Evidence vs inference clearly distinguished
    - [ ] Counter-arguments addressed
    - [ ] At least one candidate identified where preconditions exist but confirming event has not yet occurred (leading indicator, not lagging)
    """
}
