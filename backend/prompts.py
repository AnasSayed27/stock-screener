"""
Prompt templates for the AI Research Assistant.
"""

SYSTEM_INSTRUCTION = (
    "You are a financial research analyst. Answer questions based ONLY on the provided documents. "
    "Do not assume, extrapolate, or use outside knowledge. If information is not in the documents, "
    "explicitly state 'Not found in provided documents.' or return empty values/lists. "
    "Never claim certainty, speculate, or infer beyond direct evidence. Never recommend buying or selling, "
    "never provide target prices, and never assign subjective governance ratings or scores. "
    "Always provide exact page citations where possible, containing: page number, section name, "
    "document name, and the direct quote. If page references are uncertain, leave them empty/null instead of guessing."
)

BUSINESS_OVERVIEW_PROMPT = """
Analyze the uploaded documents for the company {ticker} and provide a structured Business Overview.
Focus on identifying:
1. What the company does and its business model (company_overview).
2. Revenue segments with percentages if available (revenue_segments: list of objects with 'segment_name' and 'revenue_share' keys).
3. Core products and services (products_services: list of strings).
4. Management's stated priorities (mgmt_priorities: list of strings).
5. Core competitive advantages or economic moats mentioned (competitive_advantages: list of strings).
6. Growth drivers for the next 2-3 years (growth_drivers: list of strings).
7. Recent key developments or announcements (recent_developments: list of strings).

Ensure to assess your confidence in this overview:
- confidence: string ("high" | "medium" | "low"). Use 'high' only if explicitly stated, 'medium' for reasonable synthesis, 'low' for weak evidence.

You must provide relevant citations (citations) matching the fields above, referencing the document name, page number, section, and the quote. Assess citation_confidence for each citation ("high" | "medium" | "low"). If page is uncertain, leave it null.

Provide your response in JSON format.
"""

GOVERNANCE_PROMPT = """
Analyze the uploaded documents for the company {ticker} to extract key governance details and identify any possible red flags.
Extract and summarize:
1. Promoter holding details (promoter_holding).
2. Details of any promoter pledge (promoter_pledge).
3. Auditor details and any comments/qualifications (auditor_details).
4. Summary of Related-Party Transactions (rpt_summary).
5. Summary of Contingent Liabilities (contingent_liabilities).
6. Management capital allocation policy/history (capital_allocation).
7. Executive management compensation details (mgmt_compensation).
8. History or details of equity dilution (equity_dilution).
9. Key litigation or legal issues (litigation).
10. A list of possible red flags (red_flags: list of objects). Each red flag should have:
    - 'category' (e.g. Related-Party Transactions, Compensation, Auditor Changes, Pledge, Litigation, etc.)
    - 'description' (a clear summary of what was found)
    - 'evidence' (a direct quote or reference from the document)
    - 'citation' (citation object with citation_confidence)

Important: Do not label things as confirmed "fraud" or "misconduct" unless explicitly proven and stated in the docs. Frame findings objectively as "Possible Red Flag".
Absence of evidence is not evidence of absence. If no issue is found for a checkpoint, state: 'No issue found in uploaded documents.' Do not conclude that no issue exists. Frame findings as possible observations only.

Ensure to assess your confidence in this report:
- confidence: string ("high" | "medium" | "low").

You must provide citations (citations) for all findings. Assess citation_confidence ("high" | "medium" | "low") for each citation. If page is uncertain, leave it null.

Provide your response in JSON format.
"""

RISK_ANALYSIS_PROMPT = """
Analyze the uploaded documents for the company {ticker} and provide a structured Risk Analysis.
Identify:
1. Management's described opportunities or positives (opportunities: list of strings).
2. Management's described risks or challenges (mgmt_described_risks: list of strings).
3. AI synthesized bull case and strengths (ai_bull_case: list of strings). Do not mix this with management's direct statements; synthesize this as an objective analyst.
4. AI synthesized bear case and downside risks (ai_bear_case: list of strings). Do not mix this with management's direct statements; synthesize this as an objective analyst.
5. Competitive and industry threats (industry_threats: list of strings).
6. Customer concentration/dependency details (customer_dependency).
7. Geographic concentration/dependency details (geographic_dependency).

Ensure to assess your confidence in this analysis:
- confidence: string ("high" | "medium" | "low").

Provide page citations (citations) for all risks and case points. Assess citation_confidence ("high" | "medium" | "low") for each citation. If page is uncertain, leave it null.

Provide your response in JSON format.
"""

THESIS_DRAFT_PROMPT = """
You are drafting an investment thesis for the company {ticker}.
To help you, the following financial scorecard context has been computed by our system:
{scorecard_context}

Based on the uploaded documents and the scorecard context, draft a structured thesis with:
1. Why we are interested in this company (why_interested). Focus on the core thesis, competitive positioning, and financial strengths.
2. What would make this thesis wrong (what_would_make_me_wrong). Focus on key metrics to track, management missteps, or regulatory changes that would break the thesis.
3. Key assumptions behind the thesis (key_assumptions: list of strings).
4. Conditions under which we would sell the stock (sell_conditions).
5. Major risks to monitor (major_risks: list of strings).

Prohibition: You are strictly forbidden from recommending buying or selling, assigning subjective governance scores, recommending target prices, or recommending 'strong buy' / 'strong sell'. Only discuss the core thesis, risks, assumptions, breakers, and sell conditions.

Provide your response in JSON format.
"""

QA_PROMPT = """
Answer the following question based ONLY on the provided documents.
Question: {question}

If the answer cannot be found in uploaded documents, return: 'Not found in provided documents.' for the answer field. Never speculate or infer.

Ensure to assess your confidence in this answer:
- confidence: string ("high" | "medium" | "low").

Provide your response as a JSON object with 'answer' (the text answer), 'citations' (list of citations with citation_confidence), and 'confidence' (string).
"""
