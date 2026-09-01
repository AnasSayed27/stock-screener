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
    "    Low coverage increases probability of mispricing, but high coverage is acceptable if the consensus is anchored to outdated assumptions or ignoring a segment.\n\n"
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
        "id": "government_policy",
        "name": "Government Policy → Beneficiary Mapping",
        "description": "Identify listed Indian companies that will benefit from a specific policy, subsidy, or regulation.",
        "input_label": "Describe the policy, scheme, or regulation (Optional, e.g., FAME-III scheme, chemical anti-dumping duty)",
        "input_type": "textarea",
        "required": False,
        "prompt_template": (
            "STRATEGY: Government Policy → Beneficiary Mapping\n\n"
            "USER INPUT (Context/Policy Details - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Identify listed Indian companies that will disproportionately benefit from government policy, budget allocation, or regulatory mandate — focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "PROACTIVE INSTRUCTIONS (If the USER INPUT above is empty or whitespace):\n"
            "1. Search for and discover recent (last 12-24 months) high-impact government policies, schemes, or major budget allocations in India (e.g., PLI schemes, FAME-III, green hydrogen, railway modernization, defense indigenization, etc.).\n"
            "2. Rank these policies by their likely investment significance and total addressable market (TAM) impact on listed companies.\n"
            "3. Select the top 1-2 most significant policies and perform a deep-dive investigation into them as outlined below.\n\n"
            "FOCUSED INSTRUCTIONS (If the USER INPUT above is provided):\n"
            "1. Directly investigate the user's specified policy, scheme, or regulation. Do not choose other policies.\n\n"
            "REASONING CHAIN (follow this step by step for the chosen policies):\n"
            "1. UNDERSTAND THE POLICY: Search for the specific government policy, scheme, or "
            "   budget allocation. Understand the exact mechanism — what is being mandated, "
            "   funded, or incentivized?\n"
            "2. CALCULATE THE TAM: What is the Total Addressable Market created by this policy? "
            "   How much money has the government allocated? Is funding placed in escrow "
            "   (eliminating receivable risk) or dependent on annual budget approvals?\n"
            "3. MAP THE VALUE CHAIN: Who are the direct beneficiaries? Then go deeper:\n"
            "   - Who supplies raw materials to the direct beneficiaries?\n"
            "   - Who supplies equipment or components?\n"
            "   - Who provides services (testing, certification, logistics)?\n"
            "   - Which companies are SOLE suppliers or have limited competition?\n"
            "4. FIND THE HIDDEN BENEFICIARIES: The obvious large-cap beneficiary is already "
            "   priced in. Search for small/micro-cap companies in the supply chain or those whose "
            "   revenue is about to inflect because of this policy.\n"
            "5. CHECK FOR STRUCTURAL ADVANTAGES: Among the beneficiaries, which ones have existing "
            "   capacity competitors lack, or certifications/approvals that take years to obtain?\n"
            "6. SEARCH DIRECTION — LEADING INDICATORS: Do not focus on companies that have already "
            "   received orders or approvals. Instead look for companies that have the certifications, "
            "   manufacturing capacity, and supplier relationships that would make them the most likely "
            "   future allocation winners — but have not yet received meaningful orders. The question is "
            "   not 'who won?' but 'who is best positioned to win and hasn't been recognized yet?'\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- How much of the policy's TAM has already been captured vs. what remains?\n"
            "- Are subsidies placed in escrow upfront, or are they dependent on disbursement?\n"
            "- Who gets paid FIRST in the execution chain?\n"
            "- Is there a PLI (Production-Linked Incentive) or similar scheme specifically targeting this?\n"
            "- What happens if the policy is delayed or scaled back?\n"
            "- WRONG MARKET ASSUMPTION: Is the market assuming policy implementation will be slow/delayed "
            "  when actual disbursement timelines suggest otherwise? Is the market assuming the obvious "
            "  large-cap wins when the mechanism actually favors smaller, specialized suppliers? Is the market "
            "  assuming one-cycle (election-dependent) spending when structural demand makes this multi-decade?\n\n"
            "FAILURE MODES (flag these as risks):\n"
            "- Government execution delays — policy announced but funds not released\n"
            "- Too many beneficiaries — if 50 companies compete, no one gets meaningful share\n"
            "- Policy reversal after election cycle\n"
            "- Company wins orders but lacks capacity to execute\n"
            "- B2G (business-to-government) receivable risk if no escrow mechanism\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"[specific policy/scheme name] beneficiary companies listed India\"\n"
            "- Search for \"PLI scheme [sector] approved companies list India\"\n"
            "- Search for recent order winners or contract awards related to \"[policy name]\"\n"
            "- Search for \"[sector] companies with PLI eligibility criteria capacity certification India not yet approved\"\n"
            "- Search for \"[policy sector] supplier positioning upcoming allocation India small cap\""
        )
    },
    {
        "id": "supply_chain",
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
        "id": "import_substitution",
        "name": "Import Substitution Opportunity",
        "description": "Find domestic companies manufacturing products India currently imports in large volumes.",
        "input_label": "Product or material category (Optional, e.g., solar wafers, active pharmaceutical ingredients)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Import Substitution Discovery\n\n"
            "USER INPUT (Product/material category - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find Indian companies that are beginning to domestically manufacture products currently imported "
            "in large quantities — capturing a pre-existing, guaranteed local market, focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "PROACTIVE INSTRUCTIONS (If the USER INPUT above is empty or whitespace):\n"
            "1. Search for and identify major import-substitution opportunities in India where the domestic "
            "   manufacturing ecosystem is aggressively expanding (e.g., active pharmaceutical ingredients (APIs), "
            "   electronics/semiconductors, solar wafers/ingots, specialty chemicals, defense hardware, high-end machinery).\n"
            "2. Rank these opportunities by the size of the import bill and the presence of supportive government incentives (like tariff hikes or PLI).\n"
            "3. Select the top 1-2 opportunities and perform a deep-dive investigation into listed Indian companies addressing them.\n\n"
            "FOCUSED INSTRUCTIONS (If the USER INPUT above is provided):\n"
            "1. Directly investigate the user's specified product or material category. Do not choose other products.\n\n"
            "REASONING CHAIN (follow this step by step for the chosen products):\n"
            "1. IDENTIFY IMPORT DEPENDENCIES: Find import value and details for the product.\n"
            "2. FIND DOMESTIC MANUFACTURERS: Search for Indian companies starting or scaling domestic "
            "   production, PLI scheme approvals, or capacity expansion announcements.\n"
            "3. ASSESS THE RUNWAY: Compare import value to domestic capacity, and look for tariff protections.\n"
            "4. FIND THE INFLECTION POINT: Is the company winning first major domestic orders or experiencing "
            "   regulatory mandates?\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: Prioritize companies that have achieved quality "
            "   certification parity with imports, completed capacity expansion, or passed customer "
            "   qualification audits — but have not yet won meaningful domestic orders. The capability "
            "   exists; the revenue hasn't arrived. That gap is the opportunity.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- What is the total import bill for this product category?\n"
            "- What percentage is currently being domestically manufactured?\n"
            "- Does the government have a stated target for domestic production?\n"
            "- Are there tariff protections or anti-dumping duties in place?\n"
            "- Is the Indian manufacturer cost-competitive without subsidies?\n"
            "- WRONG MARKET ASSUMPTION: Is the market assuming domestic quality can't match imports when "
            "  certification evidence shows parity has been achieved? Is the market pricing in tariff protection "
            "  as temporary when structural policy signals show permanence? Is the market assuming capacity is "
            "  the bottleneck when the bottleneck is actually customer qualification (which this company has already done)?\n\n"
            "FAILURE MODES:\n"
            "- Indian product quality doesn't match imports — customers won't switch\n"
            "- PLI subsidies expire and the company becomes uncompetitive\n"
            "- Global oversupply crashes prices, making domestic production unviable\n"
            "- Technology changes faster than the company can adapt\n"
            "- Multiple domestic players all enter simultaneously, destroying margins\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"import substitution [product name] India PLI listed\"\n"
            "- Search for \"[product name] domestic manufacturing India NSE BSE\"\n"
            "- Search for \"[product name] domestic manufacturer India BIS certification approved not yet commercial orders\"\n"
            "- Search for \"[product] import substitution India capacity commissioned ramp up upcoming\""
        )
    },
    {
        "id": "capital_cycle",
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
        "id": "hidden_earnings",
        "name": "Hidden Earnings (Conservative Accounting)",
        "description": "Find companies where heavy investment or conservative accounting suppresses reported PAT.",
        "input_label": "Sector or keywords (optional, e.g., R&D-heavy, high capex, brand investment)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Hidden Earnings Discovery\n\n"
            "USER INPUT (Focus keywords - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find Indian companies where conservative accounting practices or heavy investment phases "
            "artificially suppress reported earnings — making the stock look expensive while true cash "
            "earnings are extremely strong, focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "REASONING CHAIN (follow this step by step):\n"
            "1. IDENTIFY HEAVY INVESTMENT PHASES: Search for companies aggressively investing in capex, R&D, "
            "   or brand-building, showing flat PAT but growing cash flow.\n"
            "2. ANALYZE THE GAP: Find suppressed items (heavy depreciation policies, fully expensed R&D, "
            "   goodwill write-offs, deferred revenue).\n"
            "3. PROJECT THE INFLECTION: When capex cycle peaks, margins expand, and PAT explodes.\n"
            "4. VERIFY CASH FLOW: Ensure cash flow from operations (CFO) is healthy and growing, showing PAT is real.\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: The highest-value candidate is one where the "
            "   capex cycle is within 6-18 months of peaking but PAT is still at its most suppressed. "
            "   Look for companies that are commencing commercial production, completing asset "
            "   capitalization, or approaching the end of a stated investment cycle. Revenue and cash "
            "   flow evidence should lag the setup by 1-2 quarters.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- Is operating cash flow growing even as net income is flat or declining?\n"
            "- What specific line items are depressing earnings?\n"
            "- When does the current capex cycle or R&D phase peak?\n"
            "- What will normalized margins look like once investment phase ends?\n"
            "- Is management expensing things that competitors capitalize?\n"
            "- WRONG MARKET ASSUMPTION: Is the market reading PAT literally when cash flows tell a completely "
            "  different story? Is the market assuming the capex-driven earnings suppression is permanent when the "
            "  asset base being built will generate returns for decades? Is the market applying the wrong peer group "
            "  for valuation, missing that this company's normalized margins are structurally higher?\n\n"
            "FAILURE MODES:\n"
            "- Capex represents poor capital allocation or waste\n"
            "- Capex cycle never ends (capital treadmill)\n"
            "- Working capital manipulation explains cash flow gap\n"
            "- Competitors replicate the investment, neutralizing the advantage\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"Indian companies capex cycle peak 2025 2026\"\n"
            "- Search for \"operating cash flow PAT divergence Indian small cap BSE\"\n"
            "- Search for \"[company/sector] India capex cycle completion upcoming plant commissioning 2025 2026\""
        )
    },
    {
        "id": "corporate_restructuring",
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
        "id": "scuttlebutt",
        "name": "Scuttlebutt / Consumer Discovery [EXPERIMENTAL]",
        "description": "Discover listed companies whose products are gaining massive grassroots traction.",
        "input_label": "Trending product, consumer category, or brand (Optional, e.g., premium home decor, specialty retail)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Scuttlebutt and Consumer Product Discovery [EXPERIMENTAL]\n\n"
            "USER INPUT (Product/Brand/Category - optional):\n{context}\n\n"
            "NOTE: Web search cannot fully replicate on-the-ground observation or walking into a workshop. "
            "This strategy is experimental and focuses on surfacing product reviews, industry discussions, "
            "and professional forums.\n\n"
            "OBJECTIVE:\n"
            "Discover listed Indian companies whose products are gaining massive grassroots traction "
            "— loved by consumers or recommended by tradespeople/professionals — but not yet recognized by the stock market, focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "PROACTIVE INSTRUCTIONS (If the USER INPUT above is empty or whitespace):\n"
            "1. Search for emerging grassroots signals, consumer trends, or high-growth brand conversations in India from publicly available sources (e.g., product review aggregators, industry/trade forums, distributor insights, premiumization trends, rising adoption of new categories like electric two-wheelers, premium home appliances, specialty foods, or niche building materials).\n"
            "2. Identify the strongest consumer adoption signals or brand preferences.\n"
            "3. Investigate the company/companies behind the most promising products.\n\n"
            "FOCUSED INSTRUCTIONS (If the USER INPUT above is provided):\n"
            "1. Perform a focused scuttlebutt investigation on the user's specified category, brand, or product.\n\n"
            "REASONING CHAIN (follow this step by step for the chosen products/brands):\n"
            "1. IDENTIFY TRENDING PRODUCTS: Search consumer forums, social media, and professional trade channels.\n"
            "2. TRACE TO LISTED COMPANIES: Find who manufactures the trending brands and if the parent/subsidiary is listed.\n"
            "3. ASSESS PRODUCT-MARKET FIT: Is the product indispensable? Word-of-mouth growth? Highly sticky?\n"
            "4. CHECK COMPETITIVE RESPONSE: Defensibility and target for acquisitions by larger FMCG/industrial firms.\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: The best signal is trade/professional-channel "
            "   traction BEFORE it appears in mainstream media, investor presentations, or stock "
            "   screener metrics. Look for products being discussed in B2B procurement groups, distributor "
            "   forums, or trade communities — but where the manufacturer has zero stock market coverage.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- What products are professionals (plumbers, builders, mechanics) recommending to each other?\n"
            "- Which brand does the professional specifier insist on using?\n"
            "- Is the product being recommended through trade channels, not advertising?\n"
            "- What is the repeat purchase rate?\n"
            "- Is the company behind it a micro/small-cap that the market ignores?\n"
            "- WRONG MARKET ASSUMPTION: Is the market dismissing grassroots demand as anecdotal when "
            "  distribution channel data suggests it is structural and scaling? Is the market assuming this "
            "  is a fad when professional/trade channel adoption (not consumer buzz) is the actual signal? "
            "  Is the market unaware of the manufacturer behind the brand because the parent is classified in "
            "  a different sector?\n\n"
            "FAILURE MODES:\n"
            "- Product is a fad, not a trend\n"
            "- Larger competitor copies the product with bigger distribution\n"
            "- Company can't scale production to meet demand\n"
            "- Product loyalty is price-sensitive\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"best [product category] reviews professionals India\"\n"
            "- Search for \"[product brand name] manufacturer listed India NSE BSE\"\n"
            "- Search for \"[product category] India distributor forum contractor recommendation brand\""
        )
    },
    {
        "id": "smart_money",
        "name": "Smart Money / Insider Behavior",
        "description": "Find stocks with promoter creeping acquisition or pledge reductions and no analyst coverage.",
        "input_label": "Focus sector or market cap (optional, e.g., small cap promoter pledge reduction)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Smart Money and Insider Behavior Detection\n\n"
            "USER INPUT (Focus/Sector - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find listed Indian companies (focusing on {context} if provided, or generally) where promoters or "
            "insiders are aggressively buying shares or reducing pledges — especially in stocks with zero "
            "analyst coverage and negligible institutional interest, focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "REASONING CHAIN (follow this step by step):\n"
            "1. FIND UNUSUAL INSIDER ACTIVITY: Search for promoter creeping acquisitions, pledge reductions, "
            "   or block/bulk deals at a premium with no news catalyst.\n"
            "2. ASSESS THE ANOMALY: Look for purchases at a premium, consistent buying over 2+ quarters, "
            "   or buying weakness (not chasing strength).\n"
            "3. INVESTIGATE THE WHY: What catalyst (capex peak, new order, spin-off) is preceding this insider buying?\n"
            "4. CHECK FOR NEGLECT: Ensure the company has zero analyst coverage and low institutional holdings.\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: Focus on very recent insider buying (last 1-3 "
            "   months) in companies with no analyst coverage. The market hasn't had time to notice "
            "   or interpret the signal. Older insider purchases (12+ months ago) are likely already "
            "   researched and priced in by smart money trackers.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- Are insiders buying shares or is this just ESOP exercise?\n"
            "- Is the purchase at market price or at a significant premium?\n"
            "- Has buying been consistent over 2+ quarters?\n"
            "- What is the promoter's track record — have past purchases preceded rallies?\n"
            "- Is the company in a \"quiet period\" before results announcement?\n"
            "- WRONG MARKET ASSUMPTION: Is the market ignoring promoter buying because there is no analyst "
            "  coverage to amplify the signal? Is the market assuming the promoter knows no more than the public "
            "  when the context of the buying (open market, at premium) suggests significant asymmetric information? "
            "  Is the market's valuation model using the wrong base-year earnings when the promoter is buying "
            "  ahead of a known inflection?\n\n"
            "FAILURE MODES:\n"
            "- Insider buying is used to prop up the stock price artificially\n"
            "- Promoter buying but company fundamentals are deteriorating\n"
            "- Pledge reduction funded by other expensive debt\n"
            "- Bulk deal is a related-party transaction disguised as open-market purchase\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"promoter creeping acquisition SEBI disclosure NSE BSE recent months\"\n"
            "- Search for \"promoter pledge reduction small cap India recent\"\n"
            "- Search for \"promoter open market purchase India last 3 months zero analyst coverage\""
        )
    },
    {
        "id": "freeform",
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
    },
    {
        "id": "anomaly_discovery",
        "name": "Anomaly Discovery",
        "description": "Find listed Indian companies presenting financial, behavioral, or operational anomalies.",
        "input_label": "Focus search/anomaly type (optional, e.g., promoter premium buying, customer advances liability spike)",
        "input_type": "text",
        "required": False,
        "prompt_template": (
            "STRATEGY: Anomaly Discovery\n\n"
            "USER INPUT (Anomaly focus - optional):\n{context}\n\n"
            "OBJECTIVE:\n"
            "Find listed Indian companies presenting financial, behavioral, or operational anomalies (focusing on "
            "{context} if provided, or generally) where \"something doesn't make sense\" on the surface, "
            "but deeper analysis reveals a significant, mispriced investment opportunity, focusing on the earliest stage where the market has not yet fully priced in the implications.\n\n"
            "REASONING CHAIN (follow this step by step):\n"
            "1. SPOT THE ANOMALY: Look for contradictions in disclosures or filings:\n"
            "   - Insider/promoter buying shares at a significant premium to market price (e.g. Heran Drug).\n"
            "   - Sudden spike in current liabilities that is actually interest-free customer advances (e.g. Caplin Point).\n"
            "   - Sudden margins/earnings divergence due to structural change misunderstood as temporary.\n"
            "   - Net cash exceeding 50% of market capitalization for an active, operating business.\n"
            "2. RECONCILE THE CONTRADICTION: Search for why this exists (earnings call transcripts, director reports).\n"
            "3. EVALUATE THE UNDERLYING QUALITY: Is the core business solid? Downside protected?\n"
            "4. DEFINE THE INFLECTION POINT: What catalyst will make the financial statements clear to average screeners?\n"
            "5. SEARCH DIRECTION — LEADING INDICATORS: Focus on anomalies that have NOT yet been "
            "   flagged by screeners, financial media, or small-cap analyst notes. If the anomaly is "
            "   already in a Substack post or MoneyControl article, it is likely no longer a true "
            "   information gap. Search for contradictions in raw filings that haven't been interpreted.\n\n"
            "KEY QUESTIONS TO INVESTIGATE:\n"
            "- What looks bad on the surface but is actually good?\n"
            "- Why is the promoter buying at a premium to the market price?\n"
            "- Is a liability spike actually interest-free customer advances?\n"
            "- Is there a sudden divergence between cash generation and reported profitability?\n"
            "- WRONG MARKET ASSUMPTION: Is the market confusing accounting conservatism with business weakness? "
            "  Is the market misreading the anomaly as a risk when it is actually evidence of a structural advantage? "
            "  Has the market anchored to an outdated mental model that a specific piece of data contradicts "
            "  — but the contradiction hasn't been noticed yet?\n\n"
            "FAILURE MODES:\n"
            "- The anomaly is actually a red flag of fraud or accounting manipulation.\n"
            "- Promoter buying at a premium was a regulatory anomaly or tax-planning structure, not conviction.\n"
            "- High cash is trapped in subsidiaries and cannot be distributed.\n\n"
            "SEARCH GUIDANCE (Examples):\n"
            "- Search for \"promoter buying premium to market price India BSE NSE\"\n"
            "- Search for \"customer advances small cap companies India balance sheet anomaly\"\n"
            "- Search for \"promoter buying premium to market price India BSE NSE\"\n"
            "- Search for \"customer advances small cap companies India balance sheet anomaly filing disclosure misunderstood\""
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

