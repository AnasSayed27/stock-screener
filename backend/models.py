"""
Pydantic models for all API request / response schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Quality scoring
# ---------------------------------------------------------------------------

class CriterionResult(BaseModel):
    """Result of a single quality-check criterion."""
    name: str
    passed: bool
    value: Optional[float] = None
    threshold: str = ""          # human-readable threshold description
    weight: int = 0


class QualityScore(BaseModel):
    """Aggregate quality score with per-criterion breakdown."""
    score: float
    max_score: float
    percentage: float = 0.0
    criteria: list[CriterionResult] = []


class ScorecardTrends(BaseModel):
    """Trends formatted for frontend charting."""
    years: list[str] = Field(default_factory=list)
    revenue: list[Optional[float]] = Field(default_factory=list)
    net_income: list[Optional[float]] = Field(default_factory=list)
    fcf: list[Optional[float]] = Field(default_factory=list)
    total_debt: list[Optional[float]] = Field(default_factory=list)


class Scorecard(BaseModel):
    """Scorecard object expected by the frontend."""
    ticker: str
    company_name: str = ""
    sector: str = ""
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    total_score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    conviction: str = "Insufficient Data"
    is_financial_sector: bool = False
    criteria: list[CriterionResult] = Field(default_factory=list)
    trends: Optional[ScorecardTrends] = None


# ---------------------------------------------------------------------------
# DCF Valuation structure
# ---------------------------------------------------------------------------

class DCFAssumptions(BaseModel):
    growth_rate: Optional[float] = None
    discount_rate: Optional[float] = None
    terminal_growth: Optional[float] = None


class DCFScenario(BaseModel):
    fair_value: Optional[float] = None
    growth_rate: Optional[float] = None


class DCFScenarios(BaseModel):
    bear: Optional[DCFScenario] = None
    base: Optional[DCFScenario] = None
    bull: Optional[DCFScenario] = None


class DCFValuation(BaseModel):
    assumptions: Optional[DCFAssumptions] = None
    scenarios: Optional[DCFScenarios] = None


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

class ValuationResult(BaseModel):
    """Computed valuation metrics for a stock."""
    current_price: Optional[float] = None
    graham_number: Optional[float] = None
    earnings_yield: Optional[float] = None
    peg_ratio: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None
    dcf: Optional[DCFValuation] = None
    debt_to_equity: Optional[float] = None
    financing_drag_warning: Optional[str] = None


# ---------------------------------------------------------------------------
# Full stock analysis
# ---------------------------------------------------------------------------

class StockAnalysis(BaseModel):
    """Complete analysis bundle returned by /api/stock/{ticker}."""
    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    scorecard: Optional[Scorecard] = None
    valuation: Optional[ValuationResult] = None
    conviction: str = "Insufficient Data"
    conviction_description: str = ""
    is_financial_sector: bool = False
    data_years: int = 0
    disclaimer: str = (
        "This analysis is for educational purposes only. "
        "Always do your own research before making investment decisions."
    )


# ---------------------------------------------------------------------------
# Screen result (lightweight)
# ---------------------------------------------------------------------------

class ScreenResult(BaseModel):
    """Lightweight result used in the screener list view."""
    ticker: str
    name: str = ""
    sector: str = ""
    quality_score: float = 0.0
    max_score: float = 0.0
    quality_pct: float = 0.0
    margin_of_safety: Optional[float] = None
    conviction: str = "Insufficient Data"
    is_financial_sector: bool = False


class ScreenRequest(BaseModel):
    """Request body for the /api/screen endpoint."""
    tickers: list[str] = Field(default_factory=list)
    universe: str = "nifty500"  # "nifty50" or "nifty500"


# ---------------------------------------------------------------------------
# Thesis / Postmortem
# ---------------------------------------------------------------------------

class ThesisSnapshot(BaseModel):
    quality_score: Optional[float] = None
    max_score: Optional[float] = None
    conviction: Optional[str] = None
    current_price: Optional[float] = None
    margin_of_safety: Optional[float] = None
    sector: Optional[str] = None
    company_name: Optional[str] = None


class ThesisCreate(BaseModel):
    """Payload to create or update an investment thesis."""
    ticker: str
    why_interested: str = ""
    what_would_make_me_wrong: str = ""
    sell_conditions: str = ""
    sell_checklist: Optional[list[dict]] = None
    key_assumptions: Optional[list[str]] = None
    major_risks: Optional[list[str]] = None
    source: Optional[str] = None
    synthesis_id: Optional[str] = None
    governance: dict[str, bool] = Field(default_factory=dict)
    snapshot: Optional[ThesisSnapshot] = None


class ThesisResponse(BaseModel):
    """Stored investment thesis (includes metadata)."""
    ticker: str
    why_interested: str = ""
    what_would_make_me_wrong: str = ""
    sell_conditions: str = ""
    sell_checklist: Optional[list[dict]] = None
    key_assumptions: Optional[list[str]] = None
    major_risks: Optional[list[str]] = None
    source: Optional[str] = None
    synthesis_id: Optional[str] = None
    governance: dict[str, bool] = Field(default_factory=dict)
    snapshot: Optional[ThesisSnapshot] = None
    date_created: str = ""
    date_updated: Optional[str] = ""


class PostmortemCreate(BaseModel):
    """Payload to create a postmortem."""
    id: Optional[str] = None
    ticker: str
    entry_date: Optional[str] = None
    entry_price: Optional[float] = None
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    why_bought: str = ""
    why_sold: str = ""
    was_thesis_right: str = ""
    key_lessons: str = ""
    mistakes: str = ""


class PostmortemResponse(BaseModel):
    """Stored postmortem (includes metadata)."""
    id: str = ""
    ticker: str
    entry_date: Optional[str] = None
    entry_price: Optional[float] = None
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    why_bought: str = ""
    why_sold: str = ""
    was_thesis_right: str = ""
    key_lessons: str = ""
    mistakes: str = ""
    date_created: str = ""
    date_updated: Optional[str] = ""


# ---------------------------------------------------------------------------
# AI Research Models
# ---------------------------------------------------------------------------

class AICitation(BaseModel):
    page: Optional[int] = None         # AI-estimated page number
    section: Optional[str] = None
    document: Optional[str] = None     # which uploaded file
    quote: Optional[str] = None        # relevant excerpt
    citation_confidence: Optional[str] = None  # high, medium, or low

class AIRedFlag(BaseModel):
    category: str          # e.g., "Related-Party Transactions"
    description: str       # what was found
    evidence: str          # direct quote or reference from document
    citation: Optional[AICitation] = None

class AIRevenueSegment(BaseModel):
    segment_name: str = Field(description="Name of the segment (e.g. Domestic, International, or specific product/service line)")
    revenue_share: str = Field(description="Contribution or share of the segment (e.g. percentage like '45%' or value like '₹2,500 Cr')")

class AIBusinessOverview(BaseModel):
    company_overview: str = ""
    revenue_segments: list[AIRevenueSegment] = Field(default_factory=list)
    products_services: list[str] = Field(default_factory=list)
    mgmt_priorities: list[str] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)
    growth_drivers: list[str] = Field(default_factory=list)
    recent_developments: list[str] = Field(default_factory=list)
    citations: list[AICitation] = Field(default_factory=list)
    confidence: str = Field(default="medium", description="Confidence level: high, medium, or low")
    disclaimer: str = "AI research from uploaded documents. Verify from primary sources."

class AIGovernanceReport(BaseModel):
    promoter_holding: Optional[str] = None
    promoter_pledge: Optional[str] = None
    auditor_details: Optional[str] = None
    rpt_summary: Optional[str] = None
    contingent_liabilities: Optional[str] = None
    capital_allocation: Optional[str] = None
    mgmt_compensation: Optional[str] = None
    equity_dilution: Optional[str] = None
    litigation: Optional[str] = None
    red_flags: list[AIRedFlag] = Field(default_factory=list)
    citations: list[AICitation] = Field(default_factory=list)
    confidence: str = Field(default="medium", description="Confidence level: high, medium, or low")
    disclaimer: str = "AI-extracted governance data. Always verify from annual report."

class AIRiskAnalysis(BaseModel):
    opportunities: list[str] = Field(default_factory=list)
    mgmt_described_risks: list[str] = Field(default_factory=list)
    ai_bull_case: list[str] = Field(default_factory=list)
    ai_bear_case: list[str] = Field(default_factory=list)
    industry_threats: list[str] = Field(default_factory=list)
    customer_dependency: Optional[str] = None
    geographic_dependency: Optional[str] = None
    citations: list[AICitation] = Field(default_factory=list)
    confidence: str = Field(default="medium", description="Confidence level: high, medium, or low")
    disclaimer: str = "AI-generated risk analysis. Verify from primary sources."

class AIThesisDraft(BaseModel):
    why_interested: str = ""
    what_would_make_me_wrong: str = ""
    key_assumptions: list[str] = Field(default_factory=list)
    sell_conditions: str = ""
    major_risks: list[str] = Field(default_factory=list)
    disclaimer: str = "AI-drafted thesis. Review and edit before saving."

class AIAnswer(BaseModel):
    answer: str = ""
    citations: list[AICitation] = Field(default_factory=list)
    confidence: str = Field(default="medium", description="Confidence level: high, medium, or low")
    disclaimer: str = "AI answer based on uploaded documents only."

class AIReportMeta(BaseModel):
    """Metadata wrapper for saved reports."""
    prompt_version: str = ""
    model_name: str = ""
    generation_config: dict = Field(default_factory=dict)
    timestamp: str = ""
    generated_at: str = "" # Keep for frontend compatibility
    documents_used: list[str] = Field(default_factory=list)
    ticker: str = ""
    mode: str = ""
    report: dict = Field(default_factory=dict)  # the actual response


# ---------------------------------------------------------------------------
# Discovery Models
# ---------------------------------------------------------------------------

class DiscoveryCandidate(BaseModel):
    company_name: str = ""
    ticker: Optional[str] = None
    connection_type: str = ""
    confidence: str = "medium"
    why_now: str = ""
    reasoning: str = ""
    self_critique: str = ""
    disproving_evidence: str = ""
    risks: list[str] = Field(default_factory=list)
    what_to_verify: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    confidence_evolution: list[str] = Field(default_factory=list)


class DiscoverySearch(BaseModel):
    query: str = ""
    findings: str = ""
    sources: list[str] = Field(default_factory=list)
    phase: str = ""


class DiscoveryResult(BaseModel):
    analysis_summary: str = ""
    candidates: list[DiscoveryCandidate] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    searches_performed: list[DiscoverySearch] = Field(default_factory=list)
    disclaimer: str = "AI-generated hypotheses. Every candidate requires independent verification."
    phases_completed: int = 0
    total_search_count: int = 0


class DiscoverySummary(BaseModel):
    id: str = ""
    strategy_name: str = ""
    user_input_preview: str = ""
    candidate_count: int = 0
    created_at: str = ""


class DiscoveryMeta(BaseModel):
    id: str = ""
    strategy_id: str = ""
    strategy_name: str = ""
    user_params: dict = Field(default_factory=dict)
    model_name: str = ""
    created_at: str = ""
    result: DiscoveryResult = Field(default_factory=DiscoveryResult)


# ---------------------------------------------------------------------------
# Master Synthesis Models
# ---------------------------------------------------------------------------

class SynthesisCandidate(BaseModel):
    rank: int = 0
    company_name: str = ""
    ticker: Optional[str] = None
    convergence_count: int = 0
    strategies_found_in: list[str] = Field(default_factory=list)
    composite_conviction: str = "Medium"
    unified_thesis: str = ""
    key_catalysts: list = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    contrarian_view: str = ""
    action_items: list[str] = Field(default_factory=list)
    per_strategy_detail: list[dict] = Field(default_factory=list)


class SynthesisResult(BaseModel):
    ultimate_picks: list[SynthesisCandidate] = Field(default_factory=list)
    market_narrative: str = ""
    portfolio_considerations: str = ""
    total_candidates_analyzed: int = 0
    total_strategies_used: int = 0
    honorable_mentions: list[dict] = Field(default_factory=list)
    methodology_note: str = ""


class SynthesisMeta(BaseModel):
    id: str = ""
    created_at: str = ""
    model_name: str = ""
    strategy_ids_used: list[str] = Field(default_factory=list)
    strategy_names_used: list[str] = Field(default_factory=list)
    result: SynthesisResult = Field(default_factory=SynthesisResult)


class SynthesisSummary(BaseModel):
    id: str = ""
    created_at: str = ""
    pick_count: int = 0
    strategies_used: int = 0
    top_pick_name: str = ""


# ---------------------------------------------------------------------------
# Synthesis Chat & Verification Models
# ---------------------------------------------------------------------------

class SynthesisChatMessage(BaseModel):
    role: str = ""        # "user" | "assistant"
    content: str = ""
    timestamp: str = ""


class SynthesisChatSession(BaseModel):
    synthesis_id: str = ""
    messages: list[SynthesisChatMessage] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    generated_thesis: Optional[dict] = None




