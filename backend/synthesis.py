# -*- coding: utf-8 -*-
"""
Cross-Strategy Master Synthesis Module.
Aggregates user-selected discovery results (minimum 5) and uses the Master Synthesizer
LLM to generate a ranked portfolio of Ultimate Picks.
"""

from __future__ import annotations

import os
import json
import uuid
import time
import logging
import threading
from typing import Optional, Callable
from dotenv import load_dotenv
load_dotenv()

from google.genai import types

from config import SYNTHESIS_DIR, EVALUATOR_MODEL
from models import (
    SynthesisMeta,
    SynthesisResult,
    SynthesisCandidate,
    SynthesisSummary,
    DiscoveryMeta,
)
from discovery_prompts import MASTER_SYNTHESIS_PROMPT
from discovery import (
    get_discovery,
    get_client,
    _clean_and_parse_json,
    _is_quota_or_rate_limit_error,
    get_run_primary_key,
    switch_run_primary_key,
    reset_run_api_keys,
    interruptible_sleep,
)
from data_fetcher import get_stock_data

logger = logging.getLogger("discovery")

# Mapping keywords to shared regulatory / ecosystem clusters for portfolio cap enforcement
ECOSYSTEM_KEYWORDS: dict[str, list[str]] = {
    "cgd_pngrb": [
        "cgd", "city gas", "pngrb", "cng cascade", "gas distribution", "type-iv", "type iv",
        "gas transmission", "gas compressor", "gujarat gas", "time techno", "kirloskar pneumatic"
    ],
    "defense_mod": [
        "defense", "defence", "mod", "positive indigenization", "warship", "naval", "ordnance",
        "ammunition", "artillery", "aerospace defense", "hal", "drdo"
    ],
    "smart_meter_rdss": [
        "smart meter", "rdss", "amisp", "state discom", "prepaid meter", "energy meter"
    ],
    "railways_mor": [
        "railway", "vande bharat", "wagon", "locomotive", "rail capex", "titagarh", "ircon", "rvnl"
    ]
}


def _identify_ecosystem(candidate_text: str) -> Optional[str]:
    """Helper to detect shared regulatory / customer ecosystems from candidate text."""
    lower_text = candidate_text.lower()
    for ecosystem, keywords in ECOSYSTEM_KEYWORDS.items():
        if any(kw in lower_text for kw in keywords):
            return ecosystem
    return None


def apply_portfolio_guardrails(
    picks: list[SynthesisCandidate],
    honorable_mentions: list[dict],
    max_per_ecosystem: int = 2
) -> tuple[list[SynthesisCandidate], list[dict]]:
    """
    Enforces deterministic Python portfolio construction guardrails:
    1. Convergence Halving on High-Multiple Stocks:
       If a candidate trades at P/E > 75x, dampens its convergence multiplier:
       effective_convergence = 1 + (convergence - 1) / 2.0
    2. Ecosystem Cluster Cap:
       Limits any single regulatory body / ecosystem (e.g., CGD/PNGRB, Defense MoD, RDSS)
       to at most max_per_ecosystem picks in Ultimate Picks. Excess picks are gracefully
       demoted to Honorable Mentions.
    """
    adjusted_picks: list[tuple[SynthesisCandidate, float, Optional[str]]] = []

    for p in picks:
        # Check valuation via data_fetcher cache if ticker is present
        pe = None
        if p.ticker:
            clean_sym = p.ticker.strip().upper()
            if not clean_sym.endswith(".NS") and not clean_sym.endswith(".BO"):
                clean_sym = f"{clean_sym}.NS"
            stock_data = get_stock_data(clean_sym)
            if stock_data and isinstance(stock_data, dict):
                info = stock_data.get("info", {})
                pe = info.get("trailingPE") or info.get("forwardPE")

        orig_conv = float(p.convergence_count or len(p.strategies_found_in) or 1)
        # Apply Halving Method if P/E > 75x
        if pe is not None and pe > 75.0:
            effective_conv = 1.0 + (orig_conv - 1.0) / 2.0
            logger.info("⚡ [Convergence Halving] Applied on %s (P/E %.1fx): Conv %d -> Effective %.1f",
                        p.company_name, pe, int(orig_conv), effective_conv)
        else:
            effective_conv = orig_conv

        # Detect regulatory/customer ecosystem
        combined_text = f"{p.company_name} {p.unified_thesis} {' '.join(p.strategies_found_in)}"
        ecosystem = _identify_ecosystem(combined_text)

        adjusted_picks.append((p, effective_conv, ecosystem))

    # Re-sort picks by effective convergence descending while preserving relative ranking order
    # Stable sort by effective_convergence desc, then original rank asc
    adjusted_picks.sort(key=lambda item: (-item[1], item[0].rank))

    final_ultimate_picks: list[SynthesisCandidate] = []
    ecosystem_counts: dict[str, int] = {}
    demoted_mentions: list[dict] = list(honorable_mentions)

    for cand, eff_conv, eco in adjusted_picks:
        if eco:
            current_count = ecosystem_counts.get(eco, 0)
            if current_count >= max_per_ecosystem:
                logger.info("🛡️ [Ecosystem Cap] Demoting %s: Ecosystem '%s' reached cap of %d",
                            cand.company_name, eco, max_per_ecosystem)
                demoted_mentions.append({
                    "company_name": cand.company_name,
                    "ticker": cand.ticker,
                    "strategy_name": cand.strategies_found_in[0] if cand.strategies_found_in else "Master Synthesis",
                    "reason_for_watching": (
                        f"Demoted from Ultimate Picks to respect portfolio diversification: "
                        f"maximum exposure of {max_per_ecosystem} picks reached for regulatory ecosystem '{eco}'."
                    )
                })
                continue
            ecosystem_counts[eco] = current_count + 1

        final_ultimate_picks.append(cand)

    # Re-assign sequential ranks 1..N
    for new_rank, cand in enumerate(final_ultimate_picks, 1):
        cand.rank = new_rank

    return final_ultimate_picks, demoted_mentions

# Global cancellation flag for synthesis
_synthesis_cancel_requested = False
_synthesis_lock = threading.Lock()


def cancel_synthesis() -> None:
    """Trigger cancellation of active synthesis run."""
    global _synthesis_cancel_requested
    with _synthesis_lock:
        _synthesis_cancel_requested = True
    logger.info("🛑 Synthesis cancellation requested.")


def reset_synthesis_cancel() -> None:
    """Reset cancellation flag before starting a new synthesis run."""
    global _synthesis_cancel_requested
    with _synthesis_lock:
        _synthesis_cancel_requested = False


def is_synthesis_cancelled() -> bool:
    """Check if cancellation was requested."""
    with _synthesis_lock:
        return _synthesis_cancel_requested


def prepare_synthesis_input(discovery_ids: list[str]) -> tuple[str, int, int, list[str]]:
    """
    Loads selected discovery results and builds the Master Synthesizer prompt input.
    Returns: (formatted_prompt_text, total_candidates_count, strategy_count, strategy_names)
    """
    discoveries: list[DiscoveryMeta] = []
    strategy_names: list[str] = []
    total_candidates = 0

    for disc_id in discovery_ids:
        disc = get_discovery(disc_id)
        if disc and disc.result:
            discoveries.append(disc)
            strategy_names.append(disc.strategy_name)
            total_candidates += len(disc.result.candidates)

    if len(discoveries) < 5:
        raise ValueError(f"Master Synthesis requires at least 5 strategy results. Got {len(discoveries)}.")

    # Format candidates into structured text
    blocks = []
    for idx, disc in enumerate(discoveries, 1):
        strat_header = f"=== STRATEGY {idx}: {disc.strategy_name} ==="
        strat_date = f"Run Date: {disc.created_at}"
        strat_summary = f"Summary: {disc.result.analysis_summary}" if disc.result.analysis_summary else ""
        
        c_blocks = []
        for c_idx, c in enumerate(disc.result.candidates, 1):
            c_lines = [
                f"  CANDIDATE {c_idx}: {c.company_name} (Ticker: {c.ticker or 'N/A'})",
                f"  • Confidence: {c.confidence}",
                f"  • Connection Type: {c.connection_type}",
            ]
            if c.why_now:
                c_lines.append(f"  • Why Now: {c.why_now}")
            if c.reasoning:
                c_lines.append(f"  • Reasoning: {c.reasoning}")
            if c.self_critique:
                c_lines.append(f"  • Self-Critique: {c.self_critique}")
            if c.disproving_evidence:
                c_lines.append(f"  • Disproving Evidence: {c.disproving_evidence}")
            if c.risks:
                c_lines.append(f"  • Flagged Risks: {'; '.join(c.risks)}")
            if c.what_to_verify:
                c_lines.append(f"  • Items to Verify: {'; '.join(c.what_to_verify)}")
            if c.sources:
                c_lines.append(f"  • Sources: {'; '.join(c.sources[:3])}")
            if c.confidence_evolution:
                c_lines.append(f"  • Confidence Flow: {' → '.join(c.confidence_evolution)}")
            
            c_blocks.append("\n".join(c_lines))

        strat_block = f"{strat_header}\n{strat_date}\n{strat_summary}\n" + "\n\n".join(c_blocks)
        blocks.append(strat_block)

    full_candidates_text = "\n\n" + ("=" * 70) + "\n\n".join(blocks)

    # Token check & dynamic trimming if exceeding safety threshold (~800k chars)
    CHAR_LIMIT = 800_000
    if len(full_candidates_text) > CHAR_LIMIT:
        logger.warning("Synthesis input size (%d chars) exceeds threshold %d. Trimming secondary fields.", len(full_candidates_text), CHAR_LIMIT)
        blocks = []
        for idx, disc in enumerate(discoveries, 1):
            strat_header = f"=== STRATEGY {idx}: {disc.strategy_name} ==="
            c_blocks = []
            for c_idx, c in enumerate(disc.result.candidates, 1):
                reasoning_trimmed = c.reasoning[:400] + "..." if len(c.reasoning) > 400 else c.reasoning
                c_lines = [
                    f"  CANDIDATE {c_idx}: {c.company_name} (Ticker: {c.ticker or 'N/A'})",
                    f"  • Confidence: {c.confidence}",
                    f"  • Connection Type: {c.connection_type}",
                    f"  • Why Now: {c.why_now}",
                    f"  • Reasoning: {reasoning_trimmed}",
                    f"  • Flagged Risks: {'; '.join(c.risks)}",
                    f"  • Items to Verify: {'; '.join(c.what_to_verify)}",
                ]
                c_blocks.append("\n".join(c_lines))
            blocks.append(f"{strat_header}\n" + "\n\n".join(c_blocks))
        full_candidates_text = "\n\n" + ("=" * 70) + "\n\n".join(blocks)

    prompt = MASTER_SYNTHESIS_PROMPT.format(
        strategy_count=len(discoveries),
        total_candidates=total_candidates
    ) + full_candidates_text

    return prompt, total_candidates, len(discoveries), strategy_names


def run_master_synthesis(
    discovery_ids: list[str],
    progress_callback: Optional[Callable[[str], None]] = None
) -> SynthesisMeta:
    """
    Executes the Master Synthesis LLM pipeline across the given discovery IDs.
    Supports progress streaming, cancellation, and API key failover.
    """
    reset_synthesis_cancel()
    reset_run_api_keys()

    if progress_callback:
        progress_callback(f"Loading {len(discovery_ids)} strategy results from disk...")

    prompt, total_candidates, strategy_count, strategy_names = prepare_synthesis_input(discovery_ids)

    if progress_callback:
        progress_callback(f"Synthesizing {total_candidates} candidate findings across {strategy_count} strategies using Master AI...")

    if is_synthesis_cancelled():
        raise InterruptedError("Synthesis cancelled by user before API call.")

    # Call LLM with key failover
    max_attempts = 4
    response_text = ""
    last_error = None

    for attempt in range(1, max_attempts + 1):
        if is_synthesis_cancelled():
            raise InterruptedError("Synthesis cancelled by user.")

        primary_key_num = get_run_primary_key()
        alt_key_num = 2 if primary_key_num == 1 else 1

        try:
            client = get_client(key_num=primary_key_num)
            if not client:
                raise RuntimeError(f"Could not initialize Gemini client for Key {primary_key_num}. Check GEMINI_API_KEY in .env.")

            logger.info("🤖 Master Synthesis calling Gemini (%s) [Key %d, Attempt %d/%d]", EVALUATOR_MODEL, primary_key_num, attempt, max_attempts)

            response = client.models.generate_content(
                model=EVALUATOR_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )
            response_text = response.text or ""
            if response_text.strip():
                break
        except Exception as e:
            last_error = e
            logger.warning("Attempt %d failed on Key %d: %s", attempt, primary_key_num, e)

            if _is_quota_or_rate_limit_error(e):
                switch_run_primary_key(alt_key_num, reason=f"429 Quota limit on Key {primary_key_num}")
                if progress_callback:
                    progress_callback(f"Quota reached on Key {primary_key_num}. Switching to Key {alt_key_num}...")

            if attempt < max_attempts:
                wait_secs = attempt * 3
                if progress_callback:
                    progress_callback(f"Retrying in {wait_secs} seconds... (Attempt {attempt+1}/{max_attempts})")
                
                # Sleep in short increments to support responsive cancellation
                end_time = time.time() + wait_secs
                while time.time() < end_time:
                    if is_synthesis_cancelled():
                        raise InterruptedError("Synthesis cancelled by user.")
                    time.sleep(0.2)

    if not response_text.strip():
        raise RuntimeError(f"Master Synthesis failed after {max_attempts} attempts. Last error: {last_error}")

    if progress_callback:
        progress_callback("Parsing and structuring Master AI picks...")

    # Parse JSON
    parsed_json = _clean_and_parse_json(response_text)
    if not isinstance(parsed_json, dict):
        raise ValueError("Failed to parse Master Synthesizer response as valid JSON.")

    # Convert to Pydantic objects
    raw_picks = parsed_json.get("ultimate_picks", [])
    picks = []
    for idx, p in enumerate(raw_picks, 1):
        picks.append(
            SynthesisCandidate(
                rank=p.get("rank", idx),
                company_name=p.get("company_name", ""),
                ticker=p.get("ticker"),
                convergence_count=p.get("convergence_count", len(p.get("strategies_found_in", []))),
                strategies_found_in=p.get("strategies_found_in", []),
                composite_conviction=p.get("composite_conviction", "High"),
                unified_thesis=p.get("unified_thesis", ""),
                key_catalysts=p.get("key_catalysts", []),
                key_risks=p.get("key_risks", []),
                contrarian_view=p.get("contrarian_view", ""),
                action_items=p.get("action_items", []),
                per_strategy_detail=p.get("per_strategy_detail", []),
            )
        )

    # Apply deterministic Python portfolio guardrails (Convergence Halving & Ecosystem Cap)
    raw_honorable = parsed_json.get("honorable_mentions", [])
    final_picks, final_honorable = apply_portfolio_guardrails(picks, raw_honorable, max_per_ecosystem=2)

    synthesis_result = SynthesisResult(
        ultimate_picks=final_picks,
        market_narrative=parsed_json.get("market_narrative", ""),
        portfolio_considerations=parsed_json.get("portfolio_considerations", ""),
        total_candidates_analyzed=total_candidates,
        total_strategies_used=strategy_count,
        honorable_mentions=final_honorable,
        methodology_note=parsed_json.get("methodology_note", ""),
    )

    synthesis_meta = SynthesisMeta(
        id=str(uuid.uuid4()),
        created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        model_name=EVALUATOR_MODEL,
        strategy_ids_used=discovery_ids,
        strategy_names_used=strategy_names,
        result=synthesis_result,
    )

    # Save to local disk
    save_synthesis(synthesis_meta)

    if progress_callback:
        progress_callback("Master Synthesis complete!")

    return synthesis_meta


# ---------------------------------------------------------------------------
# Storage & Retrieval Helpers
# ---------------------------------------------------------------------------

def save_synthesis(meta: SynthesisMeta):
    """Saves a synthesis meta object to local disk as JSON atomically."""
    from security_utils import safe_join, validate_uuid
    from storage import atomic_write_json
    try:
        safe_id = validate_uuid(meta.id)
        filepath = safe_join(SYNTHESIS_DIR, f"{safe_id}.json")
        if hasattr(meta, "model_dump"):
            data = meta.model_dump()
        else:
            data = meta.dict()

        atomic_write_json(filepath, data)
        logger.info("Synthesis %s atomically saved to disk", safe_id)
    except Exception as e:
        logger.error("Failed to save synthesis %s: %s", meta.id, e)


def get_saved_syntheses() -> list[SynthesisSummary]:
    """Returns a sorted list of all saved synthesis runs, isolating corrupted files."""
    from security_utils import safe_join
    from storage import safe_read_json
    summaries = []
    if not os.path.exists(SYNTHESIS_DIR):
        return summaries

    for filename in os.listdir(SYNTHESIS_DIR):
        if not filename.endswith(".json") or filename.startswith("."):
            continue

        try:
            filepath = safe_join(SYNTHESIS_DIR, filename)
            data = safe_read_json(filepath)
            if not data or not isinstance(data, dict):
                continue

            result = data.get("result", {})
            picks = result.get("ultimate_picks", [])
            top_pick = picks[0].get("company_name", "N/A") if picks else "None"

            summaries.append(
                SynthesisSummary(
                    id=data.get("id", ""),
                    created_at=data.get("created_at", ""),
                    pick_count=len(picks),
                    strategies_used=len(data.get("strategy_ids_used", [])),
                    top_pick_name=top_pick,
                )
            )
        except Exception as e:
            logger.warning("Error reading synthesis file %s (skipping): %s", filename, e)

    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def get_synthesis(synthesis_id: str) -> Optional[SynthesisMeta]:
    """Loads a specific synthesis result by ID from disk."""
    from security_utils import safe_join, validate_uuid
    from storage import safe_read_json
    try:
        safe_id = validate_uuid(synthesis_id)
        filepath = safe_join(SYNTHESIS_DIR, f"{safe_id}.json")
    except ValueError:
        return None

    if not os.path.exists(filepath):
        return None
    try:
        data = safe_read_json(filepath)
        if data and isinstance(data, dict):
            return SynthesisMeta(**data)
        return None
    except Exception as e:
        logger.error("Failed to parse synthesis %s: %s", synthesis_id, e)
        return None


def delete_synthesis(synthesis_id: str) -> bool:
    """Deletes a saved synthesis file from disk."""
    from security_utils import safe_join, validate_uuid
    try:
        safe_id = validate_uuid(synthesis_id)
        filepath = safe_join(SYNTHESIS_DIR, f"{safe_id}.json")
    except ValueError:
        return False

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            logger.error("Failed to delete synthesis %s: %s", synthesis_id, e)
            return False
    return False
