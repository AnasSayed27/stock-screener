# -*- coding: utf-8 -*-
"""
Report-Level Cross-Candidate Verification Chat & Thesis Generator Engine.
Provides an adversarial AI dialogue interface for comparing, stress-testing, and verifying user reasoning
across ALL candidates in a Master Synthesis report, and generating battle-tested investment theses with sell checklists.
"""

from __future__ import annotations

import os
import json
import time
import logging
from typing import Optional, Generator
from dotenv import load_dotenv
load_dotenv()

from google.genai import types

from config import SYNTHESIS_CHATS_DIR, EVALUATOR_MODEL
from models import (
    SynthesisChatSession,
    SynthesisChatMessage,
    ThesisCreate,
)
from synthesis import get_synthesis
from discovery import (
    get_client,
    _clean_and_parse_json,
    _is_quota_or_rate_limit_error,
    get_run_primary_key,
    switch_run_primary_key,
)

logger = logging.getLogger("discovery")


def _get_chat_filepath(synthesis_id: str) -> str:
    """Returns absolute file path for a report-level chat session file."""
    return os.path.join(SYNTHESIS_CHATS_DIR, f"{synthesis_id}.json")


def get_synthesis_chat(synthesis_id: str) -> Optional[SynthesisChatSession]:
    """Loads saved report-level chat session from disk."""
    filepath = _get_chat_filepath(synthesis_id)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SynthesisChatSession(**data)
    except Exception as e:
        logger.error("Failed to load synthesis chat session %s: %s", synthesis_id, e)
        return None


def save_synthesis_chat(session: SynthesisChatSession) -> None:
    """Saves report-level chat session to disk."""
    os.makedirs(SYNTHESIS_CHATS_DIR, exist_ok=True)
    filepath = _get_chat_filepath(session.synthesis_id)
    try:
        data = session.model_dump() if hasattr(session, "model_dump") else session.dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to save synthesis chat session %s: %s", session.synthesis_id, e)


def delete_synthesis_chat(synthesis_id: str) -> bool:
    """Deletes saved report-level chat session file."""
    filepath = _get_chat_filepath(synthesis_id)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            logger.error("Failed to delete synthesis chat %s: %s", synthesis_id, e)
            return False
    return False


DEVILS_ADVOCATE_REPORT_PROMPT = """You are the Chief Investment Officer (CIO) and Senior Equity Research Director acting as an adversarial devil's advocate for an entire Master Synthesis investment report.

Your goal is to help the user review, compare, stress-test, and choose among ALL top picks and honorable mentions in this report with full cross-candidate context. You must challenge weak reasoning, highlight cross-candidate risks/trade-offs, verify evidence, and prevent confirmation bias.

OVERARCHING REPORT CONTEXT:
Total Strategies Analyzed: {total_strategies_used}
Total Candidates Reviewed: {total_candidates_analyzed}
Market Narrative: {market_narrative}
Portfolio & Sector Balance: {portfolio_considerations}

FULL ULTIMATE PICKS IN THIS REPORT:
{all_picks_text}

HONORABLE MENTIONS (WATCHLIST CANDIDATES):
{honorable_mentions_text}

INTERACTION INSTRUCTIONS:
1. You have complete context of ALL ultimate picks AND honorable mentions in this report. You can compare any stock against any other (including comparing ultimate picks vs watchlist honorable mentions).
2. Be direct, objective, factual, and completely un-sugarcoated.
3. If the user presents strong, evidence-backed reasoning for picking a specific stock or combination, validate it concisely and highlight confirming signals across the strategies.
4. If the user presents weak reasoning, vague speculation, or ignores key risks / contrarian views, directly challenge them and explain WHY their thinking is flawed or incomplete.
5. Keep your responses concise (2-3 crisp paragraphs max) so the comparative discussion stays sharp and actionable.
"""

THESIS_GENERATION_PROMPT = """You are an expert Chief Investment Officer.
Based on the full Master Synthesis report context and the adversarial verification discussion with the user, synthesize a finalized, high-conviction Investment Thesis and Sell Checklist for the chosen stock: {company_name} (Ticker: {ticker}).

VERIFICATION & COMPARATIVE DISCUSSION CONTEXT:
User & AI Dialogue History:
{chat_history}

Selected Stock Research Context:
- Rank: #{rank}
- Composite Conviction: {conviction}
- Strategies Found In: {strategies}
- Unified Thesis: {unified_thesis}
- Contrarian View: {contrarian_view}
- Key Catalysts: {key_catalysts}
- Key Risks: {key_risks}

OUTPUT SCHEMA CONSTRAINTS:
Respond strictly with valid JSON conforming to the following structure:
{{
  "why_interested": "Concise, battle-tested thesis (3-4 crisp sentences) stating what the company does, why it is mispriced, and what triggers re-rating, refined from the user's verified reasoning and comparative discussion.",
  "what_would_make_me_wrong": "Concise 2-3 sentence statement of specific falsifiable conditions that break this thesis.",
  "key_assumptions": [
    "Core assumption 1 behind the thesis",
    "Core assumption 2 behind the thesis"
  ],
  "major_risks": [
    "Major risk 1 to monitor",
    "Major risk 2 to monitor"
  ],
  "sell_checklist": [
    {{
      "condition": "Specific, observable trigger or metric threshold that requires selling",
      "linked_assumption": "Which core thesis assumption this trigger invalidates",
      "severity": "full_exit"
    }},
    {{
      "condition": "Secondary warning trigger",
      "linked_assumption": "Which assumption is weakened",
      "severity": "partial_trim"
    }}
  ]
}}
"""


def _format_catalysts(cats) -> str:
    """Helper to format catalysts into text."""
    if not cats:
        return "None specified"
    out = []
    for c in cats:
        if isinstance(c, dict):
            out.append(f"[{c.get('window', 'N/A')}] {c.get('catalyst', '')} ({c.get('reason', '')})")
        else:
            out.append(str(c))
    return "; ".join(out)


def process_synthesis_chat(
    synthesis_id: str,
    user_message: str = "",
    action: str = "chat",
    target_stock: str = ""
) -> Generator[str, None, None]:
    """
    Handles report-level synthesis chat messages or target thesis generation.
    Yields NDJSON chunks for streaming UI updates.
    """
    # 1. Fetch parent synthesis
    meta = get_synthesis(synthesis_id)
    if not meta or not meta.result:
        yield json.dumps({"type": "error", "message": f"Synthesis {synthesis_id} not found."}) + "\n"
        return

    res = meta.result

    # 2. Load or create report-level chat session
    session = get_synthesis_chat(synthesis_id)
    if not session:
        session = SynthesisChatSession(
            synthesis_id=synthesis_id,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            updated_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )

    # 3. Action: Chat Interaction across full report
    if action == "chat":
        if user_message.strip():
            session.messages.append(
                SynthesisChatMessage(
                    role="user",
                    content=user_message.strip(),
                    timestamp=time.strftime("%H:%M:%S")
                )
            )

        # Build text for all picks in report
        picks_blocks = []
        for p in res.ultimate_picks:
            p_text = (
                f"PICK #{p.rank}: {p.company_name} (Ticker: {p.ticker or 'N/A'})\n"
                f"  • Conviction: {p.composite_conviction} | Found in {p.convergence_count} Strategies ({', '.join(p.strategies_found_in)})\n"
                f"  • Unified Thesis: {p.unified_thesis}\n"
                f"  • Contrarian View: {p.contrarian_view or 'None'}\n"
                f"  • Catalysts: {_format_catalysts(p.key_catalysts)}\n"
                f"  • Risks: {'; '.join(p.key_risks) if p.key_risks else 'None'}"
            )
            picks_blocks.append(p_text)

        all_picks_text = "\n\n".join(picks_blocks)

        # Build text for honorable mentions
        hm_blocks = []
        if res.honorable_mentions:
            for hm in res.honorable_mentions:
                comp = hm.get("company_name", "N/A")
                tick = hm.get("ticker", "N/A")
                strat = hm.get("strategy_name", "N/A")
                reason = hm.get("reason_for_watching", "N/A")
                hm_blocks.append(f"• {comp} (Ticker: {tick}) [Strategy: {strat}] — Watchlist Reason: {reason}")
        honorable_mentions_text = "\n".join(hm_blocks) if hm_blocks else "None flagged in this report."

        system_prompt = DEVILS_ADVOCATE_REPORT_PROMPT.format(
            total_strategies_used=res.total_strategies_used,
            total_candidates_analyzed=res.total_candidates_analyzed,
            market_narrative=res.market_narrative or "N/A",
            portfolio_considerations=res.portfolio_considerations or "N/A",
            all_picks_text=all_picks_text,
            honorable_mentions_text=honorable_mentions_text,
        )

        contents = [system_prompt]
        for msg in session.messages:
            prefix = "User: " if msg.role == "user" else "Assistant: "
            contents.append(f"{prefix}{msg.content}")

        yield json.dumps({"type": "status", "message": "Analyzing reasoning against full report context & candidate options..."}) + "\n"

        response_text = ""
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            primary_key_num = get_run_primary_key()
            alt_key_num = 2 if primary_key_num == 1 else 1

            try:
                client = get_client(key_num=primary_key_num)
                if not client:
                    raise RuntimeError("Could not initialize Gemini client.")

                response = client.models.generate_content(
                    model=EVALUATOR_MODEL,
                    contents="\n\n".join(contents),
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                    ),
                )
                response_text = response.text or ""
                if response_text.strip():
                    break
            except Exception as e:
                logger.warning("Synthesis report chat attempt %d failed on Key %d: %s", attempt, primary_key_num, e)
                if _is_quota_or_rate_limit_error(e):
                    switch_run_primary_key(alt_key_num, reason="Rate limit on report chat")
                time.sleep(1)

        if not response_text.strip():
            yield json.dumps({"type": "error", "message": "Failed to get AI response. Please try again."}) + "\n"
            return

        assistant_msg = SynthesisChatMessage(
            role="assistant",
            content=response_text.strip(),
            timestamp=time.strftime("%H:%M:%S")
        )
        session.messages.append(assistant_msg)
        session.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        save_synthesis_chat(session)

        data_dict = session.model_dump() if hasattr(session, "model_dump") else session.dict()
        yield json.dumps({"type": "chat_update", "session": data_dict}) + "\n"

    # 4. Action: Generate Thesis for a Targeted Stock
    elif action == "generate_thesis":
        # Resolve target stock pick from ultimate picks or honorable mentions
        target_pick = None
        target_str = (target_stock or "").strip().lower()

        if target_str:
            for p in res.ultimate_picks:
                if (
                    str(p.rank) == target_str
                    or target_str in p.company_name.lower()
                    or (p.ticker and target_str in p.ticker.lower())
                ):
                    target_pick = p
                    break

            if not target_pick and res.honorable_mentions:
                for hm in res.honorable_mentions:
                    c_name = hm.get("company_name", "")
                    c_tick = hm.get("ticker", "")
                    if target_str in c_name.lower() or (c_tick and target_str in c_tick.lower()):
                        target_pick = SynthesisCandidate(
                            rank=99,
                            company_name=c_name,
                            ticker=c_tick,
                            convergence_count=1,
                            strategies_found_in=[hm.get("strategy_name", "Watchlist")],
                            composite_conviction="Medium",
                            unified_thesis=hm.get("reason_for_watching", "Watchlist candidate"),
                        )
                        break

        # Fallback to rank #1 if not specified or not matched
        if not target_pick and res.ultimate_picks:
            target_pick = res.ultimate_picks[0]

        if not target_pick:
            yield json.dumps({"type": "error", "message": "No valid stock candidate found for thesis generation."}) + "\n"
            return

        chat_history_str = "\n".join([f"{m.role.upper()} [{m.timestamp}]: {m.content}" for m in session.messages])
        if not chat_history_str:
            chat_history_str = "No prior dialogue. User requested direct thesis synthesis."

        prompt = THESIS_GENERATION_PROMPT.format(
            company_name=target_pick.company_name,
            ticker=target_pick.ticker or "N/A",
            rank=target_pick.rank,
            conviction=target_pick.composite_conviction,
            strategies=", ".join(target_pick.strategies_found_in),
            chat_history=chat_history_str,
            unified_thesis=target_pick.unified_thesis,
            contrarian_view=target_pick.contrarian_view or "None",
            key_catalysts=_format_catalysts(target_pick.key_catalysts),
            key_risks="; ".join(target_pick.key_risks) if target_pick.key_risks else "None",
        )

        yield json.dumps({"type": "status", "message": f"Synthesizing verified thesis & sell checklist for {target_pick.company_name}..."}) + "\n"

        response_text = ""
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            primary_key_num = get_run_primary_key()
            alt_key_num = 2 if primary_key_num == 1 else 1

            try:
                client = get_client(key_num=primary_key_num)
                if not client:
                    raise RuntimeError("Could not initialize Gemini client.")

                response = client.models.generate_content(
                    model=EVALUATOR_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                )
                response_text = response.text or ""
                if response_text.strip():
                    break
            except Exception as e:
                logger.warning("Thesis gen attempt %d failed on Key %d: %s", attempt, primary_key_num, e)
                if _is_quota_or_rate_limit_error(e):
                    switch_run_primary_key(alt_key_num, reason="Rate limit on thesis gen")
                time.sleep(1)

        if not response_text.strip():
            yield json.dumps({"type": "error", "message": "Failed to generate thesis JSON."}) + "\n"
            return

        parsed_json = _clean_and_parse_json(response_text)
        if not isinstance(parsed_json, dict):
            yield json.dumps({"type": "error", "message": "AI returned invalid thesis JSON structure."}) + "\n"
            return

        session.generated_thesis = parsed_json
        session.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        save_synthesis_chat(session)

        yield json.dumps({
            "type": "thesis_generated",
            "thesis": parsed_json,
            "ticker": target_pick.ticker,
            "company_name": target_pick.company_name,
            "rank": target_pick.rank,
            "synthesis_id": synthesis_id
        }) + "\n"
