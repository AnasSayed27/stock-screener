# -*- coding: utf-8 -*-
"""
DiscoveryLens prompt library and strategy definitions.
"""

BASE_ANALYST_PERSONA = (
    "You are an Indian equity research analyst specializing in discovering hidden "
    "investment opportunities — companies that are publicly listed but not yet widely "
    "recognized by the market.\n\n"
    "RULES FOR THE REASONING PROCESS:\n"
    "1. You have access to a search_web tool. Use it dynamically to gather real, "
    "   current information. Do not rely solely on your training data. Decide for yourself "
    "   what to search, how to search, what connections to make, and what angles to explore.\n"
    "2. Focus EXCLUSIVELY on companies listed on NSE or BSE (Indian stock exchanges).\n"
    "3. Provide ticker only when highly confident. Do not guess ticker symbols. "
    "   Company name is sufficient and is the primary identifier. If unsure, return null.\n"
    "4. Be explicit about uncertainty. Mark confidence as \"high\" only when you have "
    "   strong evidence from multiple sources. Use \"medium\" for reasonable inference "
    "   and \"low\" for speculative connections. If the evidence is weak, say so explicitly "
    "   in the confidence field and reasoning.\n"
    "5. NEVER recommend buying or selling. You generate HYPOTHESES for a human "
    "   portfolio manager to investigate further.\n"
    "6. For every claim, explain your reasoning chain — how you connected the dots.\n"
    "7. Distinguish between what you found (evidence) and what you inferred (reasoning).\n"
    "8. Think in second and third-order effects. The obvious beneficiary is already "
    "   priced in. Look deeper in the value chain.\n"
    "9. Prefer recent sources (from the last 12-24 months) for news and current events.\n"
    "10. NEVER fabricate or hallucinate details. If you do not know or are uncertain, state it clearly.\n"
)

RESEARCH_SYSTEM_PROMPT = BASE_ANALYST_PERSONA

SYNTHESIS_SYSTEM_PROMPT = BASE_ANALYST_PERSONA + (
    "11. QUALITY GATE: Do NOT limit the candidate count to a specific number range. "
    "    Instead, return every candidate where you have genuine, high-quality reasoning and evidence. "
    "    Do NOT include filler or mediocre candidates just to pad the list. If there are "
    "    multiple solid candidates, return them all. If there is only 1 or 2, return only them. "
    "    Return empty if no genuine candidates are found.\n"
    "12. MARKET MISPRICING CLASSIFICATION: For every candidate, you must classify the mispricing as one of:\n"
    "    - TYPE A (WRONG CONSENSUS): Market has looked at this company/sector and formed an incorrect assumption. State it as: 'The market currently assumes X, but evidence shows Y.'\n"
    "    - TYPE B (INVISIBLE TO MARKET): Market has never looked at this company. No consensus exists. State why it is invisible (zero coverage, misclassified sector, too small) and what trigger will force recognition: 'This company is invisible because [reason]. The market will notice it when [trigger].'\n"
    "    If you cannot classify the candidate as Type A or Type B with a specific, defensible statement, do not include the candidate.\n"
    "13. STAGE-AGNOSTIC MISPRICING FILTER: Do not filter candidates based on stock price movement alone. "
    "    Instead, evaluate whether the thesis — not the stock price — has been widely recognized and incorporated into consensus. "
    "    Prefer the earliest stage where the market has not yet fully incorporated the implications (which can be pre-event or post-event underreaction).\n"
    "14. ANALYST COVERAGE AS A SIGNAL: Analyst coverage is a signal for information asymmetry, not a hard filter. "
    "    Low coverage increases probability of mispricing, but high coverage is acceptable if the consensus is anchored to outdated assumptions or ignoring a segment.\n"
    "15. LIQUIDITY & FLOAT GATE (AVOID PENNY/ILLIQUID TRAPS): Do not recommend micro-cap companies with market cap < ₹300 Crore "
    "    or illiquid trading volumes. Promoter warrant conversions, preferential allotments, or price spikes in thin-float penny stocks "
    "    are frequently promotional signals or pump-and-dump traps lacking institutional custody. Only recommend candidates where institutional "
    "    investors can legitimately build or hold positions.\n\n"
    "OUTPUT FORMAT CONSTRAINTS:\n"
    "Return a JSON object matching the required schema. Every candidate must include:\n"
    "- company_name: Name of the company.\n"
    "- ticker: NSE/BSE ticker (or null if unsure).\n"
    "- connection_type: The role of this company in the thesis.\n"
    "- confidence: high | medium | low.\n"
    "- why_now: Why THIS moment? What has changed? Must include: (a) what changed, (b) estimated catalyst window (near-term: 0-6 months | medium-term: 6-18 months | long-term: 18+ months) with a brief reason, and (c) confirming milestone (observable event verifying the thesis).\n"
    "- reasoning: The complete reasoning chain. Must start with the [WRONG ASSUMPTION] or [INVISIBLE TO MARKET] statement, followed by evidence classified into: [OBSERVED FACTS] (verifiable data/filings), [STRONG INFERENCE] (reasoning from facts), and [HYPOTHESIS] (claims needing validation).\n"
    "- self_critique: \"Why might this specific hypothesis be wrong?\" A candidate-specific rebuttal.\n"
    "- disproving_evidence: \"What would prove this wrong?\" (What specific evidence/event would invalidate the thesis?)\n"
    "- risks: List of specific risks for this company.\n"
    "- what_to_verify: List of items to verify. The first item MUST be: 'KILLER ASSUMPTION: [the single critical assumption that, if wrong, invalidates the entire thesis]'.\n"
    "- sources: List of source links/articles used to back up this candidate."
)

COMMON_SYSTEM_PROMPT = RESEARCH_SYSTEM_PROMPT


DISCOVERY_STRATEGIES = [
    {
        "id": "policy_import_substitution",
        "category": "core",
        "name": "Policy & Domestic Replacement",
        "description": "Identify listed Indian companies benefiting from sovereign policy allocations, PLI/regulatory mandates, or tariff-protected import substitution.",
        "input_label": "Describe a policy, scheme, regulation, or imported product category (Optional, e.g., PLI electronics, solar wafers, defense indigenization)",
        "input_type": "textarea",
        "required": False,
        "prompt_template": (
            "STRATEGY: Policy & Domestic Replacement Mapping\n\n"
            "USER INPUT (Policy, Scheme, or Product Category - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Identify listed Indian companies disproportionately capturing a policy-created or tariff-protected domestic Total Addressable Market (TAM) — whether via government budget/PLI allocations, regulatory mandates, or domestic manufacturing replacing large-volume imports — focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "PROACTIVE INSTRUCTIONS (If the USER INPUT above is empty or whitespace):\n"
            "1. Search for and discover recent (last 12-24 months) high-impact government policies, budget allocations, regulatory mandates, and large-scale import-substitution opportunities in India (e.g., PLI schemes, green hydrogen, railway modernization, defense indigenization, APIs, electronics/semiconductors, solar wafers/ingots, specialty chemicals, high-end machinery).\n"
            "2. Rank these opportunities by TAM / import-bill size, presence of supportive tariff or regulatory protection (anti-dumping duties, BIS/ALMM mandates, PLI), and investment significance for listed companies.\n"
            "3. Select the top 1-2 most significant opportunities and perform a deep-dive investigation into listed Indian companies addressing them.\n\n"
            "FOCUSED INSTRUCTIONS (If the USER INPUT above is provided):\n"
            "1. Directly investigate the user's specified policy, regulation, or import-substitution product category. Do not choose other themes.\n\n"
            "REASONING CHAIN (follow this step by step for the chosen themes):\n"
            "1. UNDERSTAND THE MECHANISM & IMPORT DEPENDENCY: Identify what is being mandated, funded, incentivized, or tariff-protected, along with the total import bill and current domestic manufacturing share.\n"
            "2. CALCULATE THE TAM & FUNDING QUALITY: Quantify the addressable market and runway versus domestic capacity. Verify whether government funding is placed in escrow upfront (eliminating receivable risk) or dependent on annual budget approvals and slow PLI disbursements.\n"
            "3. MAP THE VALUE CHAIN & DOMESTIC MANUFACTURERS: Identify direct beneficiaries and Indian manufacturers scaling domestic production, then go deeper:\n"
            "   - Who supplies raw materials, equipment, or components to direct beneficiaries?\n"
            "   - Who provides testing, certification, or specialized logistics?\n"
            "   - Which companies are SOLE suppliers or have limited competition?\n"
            "4. FIND THE HIDDEN BENEFICIARIES & STRUCTURAL ADVANTAGES: Look past already-priced large caps toward small/mid-cap suppliers whose revenue is about to inflect. Verify existing capacity, cost competitiveness without subsidies, and multi-year certifications/customer qualifications.\n"
            "5. VERIFY CASH CONVERSION ON ORDER BOOKS: Where candidates boast large policy or government order books (Order-Book-to-Bill > 1.5x), verify healthy operating cash flow conversion (CFO/PAT > 0.8x) to avoid receivable-heavy fake-growth traps.\n"
            "6. SEARCH DIRECTION — LEADING INDICATORS: Do not focus only on companies that have already announced major orders or approvals. Prioritize companies that have achieved quality certification parity with imports, completed capacity expansion, or passed customer qualification audits — and are best positioned to win upcoming allocations before meaningful revenue arrives.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- How much of the policy TAM or import bill remains uncaptured vs. domestically manufactured?\n"
            "- Are subsidies placed in escrow upfront, or dependent on delayed government/PLI disbursement?\n"
            "- Are tariff protections, anti-dumping duties, or BIS/ALMM mandates structural and permanent?\n"
            "- Is the Indian manufacturer cost-competitive without subsidies, and who gets paid FIRST in the execution chain?\n"
            "- What happens if the policy is delayed, scaled back, or subsidies expire?\n"
            "- WRONG MARKET ASSUMPTION: Is the market assuming policy implementation will be delayed or that domestic quality cannot match imports when certification and disbursement evidence shows otherwise? Is the market pricing tariff protection as temporary or assuming the obvious large-cap wins when the mechanism actually favors smaller, specialized, pre-qualified suppliers?\n\n"
            "FAILURE MODES (flag these as risks):\n"
            "- Government execution delays or PLI disbursement lag — policy announced but funds not released\n"
            "- B2G (business-to-government) receivable risk if no escrow mechanism exists\n"
            "- Indian product quality fails to match imports or becomes uncompetitive once subsidies expire\n"
            "- Too many domestic players enter simultaneously or global oversupply crashes prices, destroying margins\n"
            "- Policy reversal after election cycle, or company wins orders but lacks capacity to execute\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"[specific policy/scheme name] beneficiary companies listed India\"\n"
            "- Search for \"PLI scheme [sector] approved companies list India\"\n"
            "- Search for \"import substitution [product name] India PLI tariff anti-dumping listed NSE BSE\"\n"
            "- Search for \"[product/sector] domestic manufacturer India BIS certification approved capacity commissioned upcoming\""
        )
    },
    {
        "id": "supply_chain",
        "category": "core",
        "name": "Supply Chain Dependency Mapper",
        "description": "Given a booming end-product or sector, map backward to find indispensable suppliers.",
        "input_label": "Enter a booming end-product, company, or sector (Optional, e.g., Electric Vehicles, Data Centers, Solar Panels)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Supply Chain Dependency Mapping\n\n"
            "USER INPUT (Booming sector/product/company - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Identify listed Indian companies that are indispensable suppliers in a booming supply chain — focusing on the earliest stage where the market has not yet fully priced in the implications. "
            "Focus on small listed companies that get paid BEFORE the end-product is even sold.\n\n"
            "PROACTIVE INSTRUCTIONS (If the USER INPUT above is empty or whitespace):\n"
            "1. Search for and identify currently booming industries, consumer trends, or high-growth companies in India (e.g., Electric Vehicles, Data Centers, AI Infrastructure, Solar/Renewable Energy, Defense, Premium Retail, etc.).\n"
            "2. Select the top 1-2 most promising booming areas.\n"
            "3. Map their supply chains backward to discover overlooked, niche listed beneficiaries.\n\n"
            "FOCUSED INSTRUCTIONS (If the USER INPUT above is provided):\n"
            "1. Directly investigate the user's specified sector, product, or company. Map its supply chain backward.\n\n"
            "REASONING CHAIN (follow this step by step for the chosen supply chains):\n"
            "1. IDENTIFY THE BOOM: Search for sectors or companies experiencing visible demand growth.\n"
            "2. MAP THE VALUE CHAIN BACKWARD:\n"
            "   - What raw materials go into the end product?\n"
            "   - What components are essential and non-substitutable?\n"
            "   - What equipment is needed to manufacture it?\n"
            "   - What services are required (testing, logistics, certification)?\n"
            "3. FIND THE CHOKEPOINT: In every supply chain, there is usually ONE input that is hard to "
            "   substitute, supplied by very few companies, and required regardless of which maker wins.\n"
            "4. IDENTIFY THE EARLIEST PAYER: Who gets paid first in the chain? Investing in the earliest "
            "   indispensable link reduces risk.\n"
            "5. CHECK LISTED STATUS: Search for whether these suppliers are listed on NSE/BSE.\n"
            "6. SEARCH DIRECTION — LEADING INDICATORS: Distinguish between suppliers whose revenue is "
            "   already inflecting (lagging signal — likely priced in) vs. suppliers who hold a "
            "   chokepoint position with capacity in place but demand not yet arrived. Prefer the latter. "
            "   The question is: 'Who gets paid when the boom reaches them — before it does?'\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- Who gets paid FIRST in this value chain?\n"
            "- What happens if this specific input is unavailable — does the entire chain stop?\n"
            "- How many alternative suppliers exist for this input?\n"
            "- Is the supplier's revenue already reflecting the boom, or is it about to?\n"
            "- Is there a capacity constraint that gives existing suppliers pricing power?\n"
            "- WRONG MARKET ASSUMPTION: Is the market treating a structural demand shift as a cyclical boom? "
            "  Is the market assuming multiple substitutes exist when the chokepoint input is actually "
            "  non-substitutable? Is the market pricing the supplier as commodity when switching costs "
            "  make it effectively sticky?\n\n"
            "FAILURE MODES:\n"
            "- Multiple substitutes exist — no pricing power\n"
            "- End-product boom is cyclical and near its peak\n"
            "- Supplier is dependent on a single customer (concentration risk)\n"
            "- New capacity coming online from competitors\n"
            "- Input is a commodity with no differentiation\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"[booming product/sector] supply chain India listed companies\"\n"
            "- Search for \"indispensable raw material or component for [sector/product] manufacturers India\"\n"
            "- Search for \"[product] chokepoint component suppliers India capacity expansion upcoming demand\"\n"
            "- Search for \"[sector] input material sole supplier India capacity built demand pending\""
        )
    },
    {
        "id": "hidden_monopoly",
        "category": "core",
        "name": "Hidden Monopoly / Toll Road Finder",
        "description": "Find listed Indian companies holding monopoly positions in small niche markets.",
        "input_label": "Sector or industry focus (optional, e.g., Railways, Defense, Niche Chemicals)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Hidden Monopoly and Toll Road Discovery\n\n"
            "USER INPUT (Sector focus - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find listed Indian companies that hold monopoly or near-monopoly positions in "
            "niche markets (focusing on {context} if provided, otherwise searching generally) — especially "
            "where the market is too small for large players to care but large enough to generate "
            "extraordinary returns for the incumbent, focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "REASONING CHAIN (follow this step by step):\n"
            "1. IDENTIFY NICHE SEGMENTS: Search for Indian industries where only 1-3 companies manufacture a "
            "   specific product, the product is essential, and the total market size is ₹500-5000 crore.\n"
            "2. CHECK FOR \"TOLL ROAD\" CHARACTERISTICS: Look for companies where cost of the product is "
            "   a tiny fraction of total cost, cost of failure is catastrophic, and switching costs are high.\n"
            "3. VERIFY THE MOAT: Investigate entry barriers (certifications, IP, relationships) and pricing power.\n"
            "4. CHECK FOR HIDDEN BRAND LOYALTY: Look for brand preference by professional specifiers (plumbers, "
            "   architects, builders) rather than end consumers.\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: Focus specifically on monopolies where the TAM "
            "   is about to expand (adjacent market opening, regulatory change, new end-market) but the "
            "   current stock price still reflects the old, smaller market. The pricing power already "
            "   exists; the market doesn't yet know the opportunity set is getting larger.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- How many manufacturers exist for this specific product in India?\n"
            "- Is demand captive — do customers HAVE to buy this regardless of economic cycles?\n"
            "- What are the switching costs? (certifications, re-qualification, relationship)\n"
            "- Is the company's product the industry standard that others must be compatible with?\n"
            "- What is the consequence of product failure for the customer?\n"
            "- Can the company raise prices without losing customers?\n"
            "- WRONG MARKET ASSUMPTION: Is the market valuing this at commodity multiples when the pricing power "
            "  evidence shows it behaves like a toll road? Is the market assuming the TAM is permanently small "
            "  when an adjacent market opening could 5x the addressable opportunity? Is the market ignoring this "
            "  company because its sector label is wrong (e.g., valued as industrial when it is really specialty chemicals)?\n\n"
            "FAILURE MODES:\n"
            "- Market is too small — company can never grow beyond ₹500 crore revenue\n"
            "- Technology disruption makes the product obsolete\n"
            "- Government mandates commoditization or forces competition\n"
            "- The monopoly depends on a single regulation that could change\n"
            "- Customer concentration — monopoly serves only 1-2 buyers\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"only manufacturer [product/component] India listed\"\n"
            "- Search for \"sole supplier [niche application] NSE BSE\"\n"
            "- Search for \"niche monopoly India new end market opening [sector] adjacent expansion\""
        )
    },
    {
        "id": "forensic_anomalies",
        "category": "core",
        "name": "Forensic Earnings & Behavioral Anomalies",
        "description": "Find companies where conservative accounting, balance sheet contradictions, or neglected promoter buying mask true cash earnings.",
        "input_label": "Focus anomaly or keywords (optional, e.g., capex cycle peak, customer advances, promoter creeping acquisition)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Forensic Earnings & Behavioral Anomalies Discovery\n\n"
            "USER INPUT (Focus anomaly/keywords - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find listed Indian companies (focusing on {context} if provided, or generally) where reported financials or market perception contradict underlying reality — such as conservative accounting or peaking investment cycles suppressing PAT while cash flow grows, balance-sheet anomalies misunderstood as liabilities, or genuine insider conviction in neglected stocks — focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "MANDATORY FORENSIC SAFETY GATES:\n"
            "- CASH CONVERSION GATE: Verify operating cash flow quality (CFO/PAT > 0.8x on normalized/operating basis, or growing CFO diverging positively from suppressed PAT). Reject companies with deteriorating fundamentals, persistent negative cash flow, or working-capital manipulation.\n"
            "- PROMOTER PLEDGE DISQUALIFIER: Disqualify any candidate where promoter pledge exceeds 20% of promoter holding, or where insider buying is merely ESOP exercise, thin-float warrant conversion, or promotional price propping.\n"
            "- NEGLECT FILTER FOR INSIDER SIGNALS: Treat promoter creeping acquisition (>1% open-market buying in a quarter, consistent 2+ quarter buying, buying at a premium, or pledge reduction toward <5%) as high-signal primarily in neglected stocks (<3 analysts / low institutional ownership) backed by solid core cash flows.\n\n"
            "REASONING CHAIN (follow this step by step):\n"
            "1. SPOT THE FORENSIC OR BEHAVIORAL CONTRADICTION: Search raw filings and disclosures for situations where \"something doesn't make sense\" on the surface:\n"
            "   - Heavy capex, R&D expensing, accelerated depreciation, goodwill write-offs, or deferred revenue artificially suppressing PAT while cash flow from operations (CFO) grows.\n"
            "   - Balance-sheet anomalies such as a sudden spike in current liabilities that is actually interest-free customer advances (e.g., Caplin Point), structural margin divergence misunderstood as temporary, or net cash exceeding 50% of market capitalization for an active operating business.\n"
            "   - High-conviction insider anomalies: promoter open-market creeping acquisition, purchases at a significant premium to market price, or rapid pledge reduction backed by operating cash flows (not expensive debt) in stocks with near-zero analyst coverage.\n"
            "2. RECONCILE THE CONTRADICTION & VERIFY CASH FLOW: Investigate earnings call transcripts, annual reports, and cash flow statements to confirm why the gap exists and verify healthy, growing operating cash flow (CFO/PAT > 0.8x) and downside protection.\n"
            "3. EVALUATE UNDERLYING QUALITY & CATALYST: Confirm the core business is solid and identify what precedes the inflection — capex cycle peaking within 6-18 months, commercial plant commissioning, asset capitalization completing, new order book conversion, or balance-sheet clarity.\n"
            "4. PROJECT THE INFLECTION POINT: Estimate normalized margins/earnings once the investment phase ends or the anomaly becomes obvious to mainstream screeners.\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: Focus on setups NOT yet flagged by screeners, financial media, or sell-side notes — capex cycles within 6-18 months of peaking while PAT is still suppressed, raw filing contradictions not yet widely interpreted, and very recent open-market insider buying (last 1-3 months) in neglected companies (<3 analysts).\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- What looks bad or expensive on the surface (headline PAT, P/E, liabilities) that is actually strong underneath?\n"
            "- Is operating cash flow growing (CFO/PAT > 0.8x) even as net income is flat or depressed by depreciation, R&D expensing, or capex?\n"
            "- When does the current capex cycle or R&D phase peak, and what will normalized margins look like?\n"
            "- Is a liability spike actually interest-free customer advances, or is net cash truly usable (not trapped in subsidiaries)?\n"
            "- For insider signals: is it genuine open-market buying (not ESOP/warrants), consistent over 2+ quarters or at a premium, with promoter pledge <20% and minimal analyst coverage?\n"
            "- WRONG MARKET ASSUMPTION: Is the market reading headline PAT literally or confusing accounting conservatism / balance-sheet anomalies with business weakness? Is the market assuming capex-driven earnings suppression is permanent, or ignoring asymmetric promoter open-market buying because zero analyst coverage exists to amplify the signal?\n\n"
            "FAILURE MODES:\n"
            "- Capex represents poor capital allocation, waste, or an endless capital treadmill\n"
            "- The anomaly is actually a red flag of fraud, accounting manipulation, or working-capital distortion\n"
            "- High cash is trapped in subsidiaries and cannot be distributed\n"
            "- Insider buying is promotional propping, related-party bulk deal, ESOP/warrant noise, or pledge reduction funded by expensive debt while fundamentals deteriorate\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"Indian companies capex cycle peak completion commissioning 2025 2026\"\n"
            "- Search for \"operating cash flow PAT divergence Indian small cap NSE BSE\"\n"
            "- Search for \"customer advances small cap companies India balance sheet anomaly filing disclosure\"\n"
            "- Search for \"promoter creeping acquisition open market purchase premium SEBI disclosure NSE BSE zero analyst coverage\""
        )
    },
    {
        "id": "capital_cycle",
        "category": "core",
        "name": "Capital Cycle / Trough Survivor",
        "description": "Find consolidated industries in deep cyclical troughs where capacity expansions have frozen.",
        "input_label": "Sector or industry focus (optional, e.g., Textiles, Sugar, Paper, Real Estate)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Capital Cycle and Trough Survivor Discovery\n\n"
            "USER INPUT (Sector focus - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find sectors (focusing on {context} if provided, or generally) currently in deep cyclical "
            "distress where weak players are exiting and strong survivors will inherit a consolidated "
            "market with pricing power — focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "MANDATORY DOMAIN GATE — IMPORT DUMPING & VERTICAL INSULATION:\n"
            "Domestic competitor closures or capacity freezes alone DO NOT create pricing power if cheap foreign imports "
            "(e.g., zero-duty imports from China, ASEAN, or FTA partners) can freely flood the Indian market, or if raw material "
            "spread volatility crushes margins. For any candidate in a capital cycle trough (e.g. paper, textiles, chemicals, metals):\n"
            "1. TARIFF / REGULATORY SHIELD: Verify whether the domestic market has active tariff protection (anti-dumping duties, "
            "   countervailing duty, ALMM, or Bureau of Indian Standards mandatory certification). Reject candidates whose product "
            "   faces unrestricted zero-duty import dumping.\n"
            "2. COST INSULATION & FORWARD INTEGRATION: If tariff protection is absent, the survivor MUST possess defensive insulation: "
            "   substantial captive power (>=35% renewable/thermal) or captive raw materials, PLUS downstream value-added forward "
            "   integration (e.g., converting commodity yarn to export garments). Reject standalone, single-stage commodity processors.\n\n"
            "REASONING CHAIN (follow this step by step):\n"
            "1. IDENTIFY DISTRESSED SECTORS: Look for sectors where stock prices have crashed 40-70%, companies "
            "   are reporting losses, and capex has completely frozen.\n"
            "2. ASSESS CAPITAL CYCLE: Has capacity addition stopped? Are weaker competitors shutting down or running out of cash?\n"
            "3. FIND THE SURVIVORS: Identify companies in this sector that are still profitable, have low debt, "
            "   long operating history, and strong promoter integrity.\n"
            "4. CALCULATE RECOVERY UPSIDE: Survivor inherits market share, supply contracts, and gains huge pricing "
            "   power when demand returns (operating leverage).\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: The best entry is before capacity exits are "
            "   complete and before demand recovery is visible in reported numbers. Look for early "
            "   signals: competitor capacity shutdowns announced, production curtailments, distressed "
            "   debt sales — signs the bottom is forming but not yet reflected in the survivor's revenue.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- What inning of distress are we in? Has the worst of the pain been felt?\n"
            "- Are competitors actually shutting down capacity or just pausing?\n"
            "- Can the survivor company finance itself through the trough without dilution?\n"
            "- What is the trigger for the cycle to turn?\n"
            "- Are insiders buying shares in the distressed companies?\n"
            "- WRONG MARKET ASSUMPTION: Is the market assuming the trough is permanent when supply destruction "
            "  and demand recovery signals suggest the turn is imminent? Is the market applying trough-era multiples "
            "  to a company whose operating leverage will make earnings explode at even modest recovery? Is the "
            "  market pricing the survivor as if it shares risk with the failed players, when its balance sheet is "
            "  actually pristine?\n\n"
            "FAILURE MODES:\n"
            "- Structural decline, not cyclical — industry never recovers\n"
            "- Government intervention prevents natural consolidation\n"
            "- Survivor company's debt is larger than it appears\n"
            "- Cycle lasts longer than the company's cash reserves\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"sector consolidation distressed industry India listed companies\"\n"
            "- Search for \"capacity utilization shutdown [sector name] India\"\n"
            "- Search for \"[sector] India capacity shutdown plant closure 2024 2025 consolidation\"\n"
            "- Search for \"[sector] survivor low debt India trough distress turnaround upcoming\""
        )
    },
    {
        "id": "corporate_restructuring",
        "category": "core",
        "name": "Corporate Restructuring / Special Situations",
        "description": "Find spinoffs, demergers, or restructurings creating forced institutional selling.",
        "input_label": "Demerger/Restructuring focus keywords (optional)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Corporate Restructuring and Special Situations\n\n"
            "USER INPUT (Focus keywords - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find listed Indian companies undergoing spinoffs, demergers, or restructurings "
            "where institutional selling pressure creates artificially depressed prices, focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "MANDATORY DOMAIN GATE — STATUTORY TIMELINE & CATALYST AUTHORITY:\n"
            "Differentiate clearly between two types of special situations:\n"
            "1. CLASS A (FAST / RULE-BOUND CATALYSTS): Exchange-mandated mechanisms (e.g. SEBI special call auctions for holding "
            "   companies, tender-offer buybacks, or Cabinet-notified incentive lists) execute on predictable, fast timelines (0-3 months).\n"
            "2. CLASS B (MULTI-AGENCY STATUTORY RESTRUCTURINGS): Composite schemes, NCLT demergers, and capital reductions require "
            "   sequential approvals from NCLT benches, MCA, regional directors, SEBI/exchanges, secured creditor consortia, and sectoral regulators (PNGRB, RBI, etc.). "
            "   Under Indian corporate jurisprudence, these routinely take 12 to 24 months. DO NOT assume a '30-to-90 day forced selling mispricing' "
            "   for a pre-NCLT or court-stage demerger. The company is likely 'dead money' or exposed to operational drag during this window. "
            "   Only mark a demerger catalyst as near-term (0-6m) if final NCLT approval has been sealed and the formal Record Date is gazetted.\n\n"
            "REASONING CHAIN (follow this step by step):\n"
            "1. FIND RECENT CORPORATE ACTIONS: Search for demergers, spinoffs, scheme of arrangements, or NCLT exits.\n"
            "2. IDENTIFY INSTITUTIONAL SELLING: Spot new small entities dumped by mutual funds or index funds "
            "   due to size mandates or index exclusion.\n"
            "3. CHECK INSIDER INCENTIVES: Look for promoters increasing stakes or allocating stock options in the demerged entity.\n"
            "4. VALUE THE PARTS: Calculate if the sum of parts is worth more than the pre-demerger parent conglomerate.\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: The best entry is during or immediately after "
            "   institutional forced selling — before the new entity has established standalone analyst "
            "   coverage, standalone earnings visibility, or re-rating by the market. Search specifically "
            "   for demergers within the last 3-12 months that have not yet been picked up by sell-side.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- Why is the demerger/restructuring happening?\n"
            "- Are institutions being forced to sell for mandate reasons (not fundamental reasons)?\n"
            "- What are insiders doing with their shares in the new entity?\n"
            "- What is the standalone business quality of the demerged entity?\n"
            "- Is there analyst coverage of the new entity, or is it in a \"coverage vacuum\"?\n"
            "- WRONG MARKET ASSUMPTION: Is the market treating the demerged entity as a tail risk when it is "
            "  actually the highest-quality part of the old conglomerate? Is institutional forced selling "
            "  creating a price that has no relationship to the standalone business quality? Is the market "
            "  applying the parent's discount to a business that deserves a completely different multiple as "
            "  an independent entity?\n\n"
            "FAILURE MODES:\n"
            "- Demerger is used to dump bad assets or debt on minority shareholders\n"
            "- New entity has no standalone viability\n"
            "- Promoter uses restructuring to increase their stake cheaply (minority dilution)\n"
            "- Regulatory/legal challenges delay or unwind the restructuring\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"demerger record date India 2025 2026\"\n"
            "- Search for \"spinoff new listing NSE BSE promoter buying\"\n"
            "- Search for \"demerger listing India 2024 2025 no analyst coverage institutional selling\""
        )
    },
    {
        "id": "freeform",
        "category": "custom",
        "name": "Free-form Discovery",
        "description": "Run a customized discovery query or test an investment hypothesis.",
        "input_label": "Enter your specific query, sector, or investment hypothesis",
        "input_type": "textarea",
        "required": True,
        "prompt_template": (
            "STRATEGY: Free-form Discovery Research\n\n"
            "USER INPUT (Investor observation/hypothesis):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Investigate the user's specific question, observation, or hypothesis: '{context}'. "
            "Identify listed Indian companies that could benefit from or be affected by it.\n\n"
            "GUARDRAILS (Stricter Constraints):\n"
            "- Ensure the user's input contains a genuine investment-related hypothesis or observation. "
            "  Do not speculate on general queries, political opinions, or non-corporate events.\n"
            "- Return candidates ONLY if there is clear, verifiable evidence. If the query is vague "
            "  or evidence is weak, return an empty candidate list and document the exact limitations "
            "  in the \"limitations\" field. Do not guess or invent connections.\n"
            "- Strictly enforce the ticker rules: if the ticker is not 100% verified, return null.\n"
            "- Reject speculative connections that rely on more than 3 levels of unverified assumptions.\n\n"
            "INSTRUCTIONS:\n"
            "1. UNDERSTAND THE CORE QUESTION: What is the investor really asking?\n"
            "2. RESEARCH THOROUGHLY: Use your search tool to gather current news, reports, and details.\n"
            "3. MAP TO LISTED COMPANIES: Connect findings to specific Indian listed companies. Explain "
            "   the reasoning chain, confidence levels, risks, and verify items.\n"
            "4. THINK IN SECOND-ORDER EFFECTS: Find pick-and-shovel players or inputs that become scarce.\n"
            "5. BE HONEST ABOUT LIMITATIONS: Do not fabricate connections. If evidence is lacking, state it.\n"
            "6. WRONG MARKET ASSUMPTION: Explicitly identify what assumption the market is currently making "
            "   about this company or sector that this thesis suggests is wrong.\n"
            "7. SEARCH DIRECTION — LEADING INDICATORS: Wherever possible, identify companies where the "
            "   preconditions for the thesis are in place but the confirming event hasn't occurred yet. "
            "   The most valuable candidates are those where the market hasn't started watching.\n\n"
            "Apply the reasoning patterns of the best analysts:\n"
            "- Damani: \"Is this an astonishing bargain relative to the TAM?\"\n"
            "- Bharaddia: \"Is conservative accounting hiding true profitability?\"\n"
            "- Marks: \"Is the market pricing in failure when survival is likely?\"\n"
            "- Kedia: \"Does this company fit SMILE?\"\n"
            "- Lynch: \"Can I explain why this company will grow in terms a child would understand?\"\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Adapt your searches directly to search for listed companies matching the user's observation.\n"
            "- Search at least 2-3 times from different angles to cross-verify findings."
        )
    }
]


MASTER_SYNTHESIS_PROMPT = """You are the Chief Investment Officer (CIO) at a top-tier Indian equity research fund.

Your research team has independently run {strategy_count} different analytical strategies across the Indian stock market. Each strategy used a completely different analytical lens (e.g. government policy beneficiaries, supply chain chokepoints, accounting anomalies, corporate restructuring, hidden monopolies, capital cycle troughs, import substitution, etc.) to discover high-conviction investment candidates.

You are now reviewing ALL their research findings together for the first time across {total_candidates} candidate mentions.

YOUR MANDATE:
Analyze all candidates across all {strategy_count} selected strategy runs and synthesize them into a single, master-ranked "Ultimate Picks" portfolio (aim for 5-10 top picks, prioritized by conviction and thesis strength).

CRITICAL EVALUATION & STYLE CONSTRAINTS:
1. CONCISE & BEGINNER-FRIENDLY TONE:
   Reason deeply internally, but write all final text in concise, plain-English language that any beginner investor can immediately digest. Avoid jargon.
   - `unified_thesis`: 3-4 crisp sentences max. Explain simply: (a) what the company does/role, (b) why the market is mispricing it, and (c) what main trigger unlocks value.
   - `contrarian_view`, `market_narrative`, and `portfolio_considerations`: 2-3 concise, direct sentences each.

2. INDEPENDENT CONVERGENCE SIGNAL:
   Companies discovered by multiple independent strategies carry an exceptionally strong signal. If a company shows up in Strategy A (Gov Policy) AND Strategy B (Supply Chain Chokepoint) AND Strategy C (Anomaly Discovery), that represents multi-angle agreement. Higher convergence count should generally elevate a candidate, UNLESS the underlying evidence in those strategies is weak or redundant.

3. THESIS & EVIDENCE QUALITY:
   Do not rely solely on candidate count. A company discovered by only 1 strategy with profound, multi-source evidence and a strong wrong-consensus thesis can beat a company discovered by 2 strategies with shallow reasoning. Judge the actual depth of reasoning, self-critique, and disproving evidence.

4. THESIS REINFORCEMENT vs. CONTRADICTIONS:
   Evaluate how different strategy findings interact. Does Strategy A's finding about capex expansion REINFORCE Strategy B's finding about order book growth? Or does Strategy C flag a financial/governance risk that invalidates Strategy A's thesis? Explicitly note these cross-strategy synergies or conflicts.

5. PORTFOLIO-LEVEL DIVERSIFICATION & NARRATIVE:
   Avoid picking candidates that all depend on the exact same macroeconomic driver (e.g. 5 defense suppliers). Ensure diversity of sectors, catalyst timelines (near-term 0-6m vs mid-term 6-18m), and risk profiles.

6. AGGREGATED RISK & CONTRARIAN CHECK:
   Consolidate all risks flagged across strategies. In addition, articulate a "contrarian view" — what is a key risk or blind spot that NONE of the strategies considered?

7. CONTRARIAN SPOT-COMMODITY & PEAK-CYCLE RISK PENALTY:
   If a candidate's thesis relies on:
   (a) Peak spot commodity rates (e.g. exceptionally high tanker charter rates, peak shipping freight, or abnormal crack spreads),
   (b) Unhedged commodity spreads or gas allocation changes that can instantly compress margins, or
   (c) An unapproved, multi-year court demerger/restructuring scheme subject to NCLT/creditor delays,
   you MUST penalize its rank. NEVER rank such candidates as #1 or #2 over asset-light, net-cash monopolies or mission-critical certified suppliers with long-term order books.

8. BALANCE SHEET & CASH FLOW DISCIPLINE:
   Prioritize companies with net-cash balance sheets, positive operating cash flow, and high ROIC. Do not elevate companies burdened with heavy net debt or execution bottlenecks into top conviction tiers purely based on narrative excitement.

OUTPUT JSON SCHEMA REQUIREMENT:
Respond strictly with valid JSON conforming to the following structure:
{{
  "ultimate_picks": [
    {{
      "rank": 1,
      "company_name": "Exact Full Company Name",
      "ticker": "NSE/BSE Ticker or null",
      "convergence_count": 3,
      "strategies_found_in": ["Strategy Name 1", "Strategy Name 2"],
      "composite_conviction": "Very High",
      "unified_thesis": "Concise 3-4 sentence plain-English synthesis explaining why this company is a top pick.",
      "key_catalysts": [
        {{
          "catalyst": "Specific event or operational trigger",
          "window": "0-6m",
          "reason": "Brief reason for this timeframe (e.g. Q3 earnings, record date, plant commissioning)"
        }}
      ],
      "key_risks": ["Merged & deduplicated cross-validated risks across all strategies"],
      "contrarian_view": "What could go wrong that none of the strategy analyses caught?",
      "action_items": ["Specific fundamental & financial items to verify next in StockLens"],
      "per_strategy_detail": [
        {{
          "strategy_name": "Strategy Name 1",
          "confidence": "high",
          "key_takeaway": "Short 1-2 sentence summary of why this specific strategy picked it"
        }}
      ]
    }}
  ],
  "market_narrative": "A high-level overview of the overarching market themes and economic forces connecting your top picks.",
  "portfolio_considerations": "Strategic commentary on sector concentration, market cap balance, risk distribution, and catalyst timing across the picks.",
  "total_candidates_analyzed": {total_candidates},
  "total_strategies_used": {strategy_count},
  "honorable_mentions": [
    {{
      "company_name": "Company Name",
      "ticker": "Ticker or null",
      "strategy_name": "Strategy Name",
      "reason_for_watching": "Why this single-strategy pick is worth tracking even if not in the top ultimate picks"
    }}
  ],
  "methodology_note": "A brief explanation of how you synthesized the findings."
}}
"""

