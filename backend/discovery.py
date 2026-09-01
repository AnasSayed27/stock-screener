# -*- coding: utf-8 -*-
"""
Core module for DiscoveryLens. Manages agentic web search, Tavily integration,
Gemini API calls, and discovery run persistence.
"""

import os
import json
import re
import time
import uuid
import logging
import urllib.request
import urllib.parse
import collections
import threading
from datetime import datetime, timezone
from typing import Optional, Any, Callable

from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import AI_MODEL, EVALUATOR_MODEL, DISCOVERY_DIR, GROQ_API_KEY
from ai_research import get_client, get_gemini_key
from models import (
    DiscoveryCandidate,
    DiscoverySearch,
    DiscoveryResult,
    DiscoverySummary,
    DiscoveryMeta
)
from discovery_prompts import RESEARCH_SYSTEM_PROMPT, SYNTHESIS_SYSTEM_PROMPT, DISCOVERY_STRATEGIES
from discovery_phases import (
    PHASE_1_LANDSCAPE_PROMPT,
    PHASE_2_CORRECTION_PROMPT,
    PHASE_3_DEEPDIVE_PROMPT,
    PHASE_4_VERIFICATION_PROMPT,
    PHASE_5_SYNTHESIS_PROMPT,
    DEPTH_LOOP_CONTINUATION_PROMPT,
    EVALUATOR_PROMPT,
    STRATEGY_COVERAGE_CHECKLISTS
)
from usage_tracker import increment_tavily, increment_gemini
from discovery_tools import get_discovery_gemini_tools, execute_discovery_tool, tool_search_web

logger = logging.getLogger(__name__)


def _repair_json(text: str) -> str:
    """
    Attempt to repair common JSON generation issues from LLMs:
    - Trailing commas before } or ]
    - Unescaped control characters (newlines, tabs) inside strings
    - Truncated JSON (missing closing brackets)
    """
    # 1. Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # 2. Escape unescaped control characters inside JSON string values
    # This handles literal newlines/tabs that LLMs sometimes put inside strings
    def _escape_control_chars(match):
        s = match.group(0)
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return s

    # Match JSON string values (between unescaped double quotes)
    text = re.sub(r'"(?:[^"\\]|\\.)*"', _escape_control_chars, text, flags=re.DOTALL)

    # 3. Fix truncated JSON — close open strings and balance brackets
    # Check if there's an unclosed string (odd number of unescaped quotes)
    in_string = False
    i = 0
    while i < len(text):
        if text[i] == '\\' and in_string:
            i += 2  # skip escaped character
            continue
        if text[i] == '"':
            in_string = not in_string
        i += 1
    if in_string:
        text += '"'

    # Remove any trailing comma or colon after closing the string
    text = re.sub(r'[,:]\s*$', '', text)

    # Balance brackets in correct nesting order using a stack
    stack = []
    in_str = False
    idx = 0
    while idx < len(text):
        ch = text[idx]
        if ch == '\\' and in_str:
            idx += 2
            continue
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch in ('{', '['):
                stack.append('}' if ch == '{' else ']')
            elif ch in ('}', ']'):
                if stack:
                    stack.pop()
        idx += 1
    # Close in reverse order (innermost first)
    text += ''.join(reversed(stack))

    return text


def _clean_and_parse_json(response_text: str) -> dict:
    """
    Clean code blocks, repair common LLM JSON issues, and parse to dict.
    Uses a multi-strategy approach:
      1. Direct parse
      2. Repair (trailing commas, control chars, bracket balancing)
      3. Progressive line-trimming + repair (handles LLM tail duplication)
      4. JSON object extraction (handles extra text around JSON)
    Raises json.JSONDecodeError if all strategies fail.
    """
    # Strip markdown code blocks
    if response_text.startswith("```"):
        lines = response_text.splitlines()
        if lines[0].startswith("```json") or lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    # Strategy 1: Try direct parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Try with repair
    try:
        repaired = _repair_json(response_text)
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Progressive line-trimming + repair
    # Handles LLM tail-duplication where the model repeats text and omits closing }
    text_lines = response_text.rstrip().split('\n')
    for trim_count in range(1, min(len(text_lines), 6)):
        trimmed = '\n'.join(text_lines[:-trim_count])
        if not trimmed.strip():
            break
        try:
            repaired = _repair_json(trimmed)
            result = json.loads(repaired)
            logger.debug("JSON recovered by trimming %d trailing line(s)", trim_count)
            return result
        except json.JSONDecodeError:
            continue

    # Strategy 4: Extract the first complete JSON object from the text
    match = re.search(r'\{', response_text)
    if match:
        depth = 0
        in_str = False
        skip_next = False
        start = match.start()
        for i in range(start, len(response_text)):
            if skip_next:
                skip_next = False
                continue
            ch = response_text[i]
            if ch == '\\' and in_str:
                skip_next = True  # skip the escaped character
                continue
            if ch == '"':
                in_str = not in_str
            elif not in_str:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        extracted = response_text[start:i + 1]
                        try:
                            return json.loads(extracted)
                        except json.JSONDecodeError:
                            break  # extraction found a block but it's still bad

    # If all strategies fail
    raise json.JSONDecodeError("Could not extract valid JSON", response_text, 0)


class DiscoveryCancelledException(Exception):
    """Raised when a discovery or research task is cancelled by user or signal."""
    pass


_cancel_requested = threading.Event()


def cancel_discovery() -> None:
    """Trigger global cancellation signal to stop active discovery runs."""
    logger.info("🛑 Global discovery cancellation requested.")
    _cancel_requested.set()


def reset_cancellation() -> None:
    """Clear cancellation signal before starting a new run."""
    _cancel_requested.clear()


def is_cancellation_requested() -> bool:
    """Check if cancellation has been requested."""
    return _cancel_requested.is_set()


def check_cancellation() -> None:
    """Check cancellation flag and raise exception if set."""
    if _cancel_requested.is_set():
        raise DiscoveryCancelledException("Process stopped by user request.")


def interruptible_sleep(duration: float, check_interval: float = 0.1) -> None:
    """Sleep in short intervals, periodically checking for cancellation."""
    end = time.time() + duration
    while time.time() < end:
        check_cancellation()
        to_sleep = min(check_interval, max(0.0, end - time.time()))
        if to_sleep > 0:
            time.sleep(to_sleep)


# Module-level state tracking active keys & exhaustion per role for current discovery run
_role_active_keys: dict[str, int] = {"research": 1, "evaluator": 1, "synthesis": 1}
_role_exhausted_keys: dict[str, set[int]] = {"research": set(), "evaluator": set(), "synthesis": set()}
_exhausted_models: set[str] = set()
_run_state_lock = threading.Lock()


def reset_run_api_keys() -> None:
    """Reset active API keys, exhausted keys, and exhausted models at start of a new run."""
    global _role_active_keys, _role_exhausted_keys, _exhausted_models
    with _run_state_lock:
        _role_active_keys = {"research": 1, "evaluator": 1, "synthesis": 1}
        _role_exhausted_keys = {"research": set(), "evaluator": set(), "synthesis": set()}
        _exhausted_models = set()
        logger.info("🔑 API Key preferences and model fallback states reset for new research run.")


def get_role_key(role: str = "research") -> int:
    """Get current active key number for a given role (1 or 2)."""
    with _run_state_lock:
        return _role_active_keys.get(role, 1)


def is_role_key_exhausted(role: str, key_num: int) -> bool:
    """Check if a specific key is permanently exhausted for this role in the current run."""
    with _run_state_lock:
        return key_num in _role_exhausted_keys.get(role, set())


def mark_role_key_exhausted(role: str, key_num: int, reason: str = "") -> int:
    """
    Mark a key as exhausted for a specific role and switch that role to the backup key.
    Returns the new active key number for that role.
    """
    global _role_active_keys, _role_exhausted_keys
    with _run_state_lock:
        if role not in _role_exhausted_keys:
            _role_exhausted_keys[role] = set()
        _role_exhausted_keys[role].add(key_num)
        
        backup_key = 2 if key_num == 1 else 1
        _role_active_keys[role] = backup_key
        logger.warning(
            "🔑 [%s] Key %d permanently marked exhausted for this run. Switched %s to Key %d. Reason: %s",
            role.upper(), key_num, role, backup_key, reason
        )
        return backup_key


def mark_model_exhausted(model_name: str, reason: str = "") -> None:
    """
    Permanently mark a model as unavailable for the rest of the research run.
    Forces all subsequent phases to immediately fallback to AI_MODEL without retrying.
    """
    global _exhausted_models
    with _run_state_lock:
        _exhausted_models.add(model_name)
        logger.warning(
            "⚠️ Model '%s' permanently marked exhausted/unavailable for this run. Reason: %s",
            model_name, reason
        )


def is_model_exhausted(model_name: str) -> bool:
    """Check if a model is permanently marked exhausted for this run."""
    with _run_state_lock:
        return model_name in _exhausted_models


# Backward-compatible aliases
def get_run_primary_key() -> int:
    return get_role_key("research")


def switch_run_primary_key(new_key_num: int, reason: str = "") -> None:
    old_key = 2 if new_key_num == 1 else 1
    mark_role_key_exhausted("research", old_key, reason)


def _is_quota_or_rate_limit_error(e: Exception) -> bool:
    """Check if an exception is due to 429 RESOURCE_EXHAUSTED or quota limits."""
    err_str = str(e).upper()
    return any(term in err_str for term in [
        "429",
        "RESOURCE_EXHAUSTED",
        "QUOTA EXCEEDED",
        "RATE_LIMIT",
        "TOO MANY REQUESTS"
    ])


# Global rate limiting state for Gemini API calls: 12 calls per minute
_gemini_call_timestamps = collections.deque()
_gemini_limiter_lock = threading.Lock()

def _wait_for_gemini_rate_limit(progress_callback: Optional[Callable[[str], None]] = None) -> None:
    """
    Ensure no more than 12 Gemini API calls per minute.
    If the limit is reached, sleep until the oldest call is more than 60 seconds old.
    """
    check_cancellation()
    with _gemini_limiter_lock:
        now = time.time()
        # Remove timestamps older than 60 seconds
        while _gemini_call_timestamps and now - _gemini_call_timestamps[0] > 60.0:
            _gemini_call_timestamps.popleft()
            
        if len(_gemini_call_timestamps) >= 12:
            # We must wait until the oldest timestamp is older than 60 seconds
            wait_time = _gemini_call_timestamps[0] + 60.0 - now
            if wait_time > 0:
                logger.info("Gemini API rate limit reached (12/min). Waiting for %.2f seconds...", wait_time)
                if progress_callback:
                    progress_callback(f"Rate limit reached. Pausing for {wait_time:.1f}s...")
                interruptible_sleep(wait_time)
                # Re-calculate 'now' after sleeping
                now = time.time()
                
            # Clean up again just in case
            while _gemini_call_timestamps and now - _gemini_call_timestamps[0] > 60.0:
                _gemini_call_timestamps.popleft()
                
        _gemini_call_timestamps.append(now)


def run_tavily_search(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
    progress_callback: Optional[Callable[[str], None]] = None
) -> tuple[str, list[str]]:
    """
    Search the web using Tavily API with graceful retry support.
    Delegates to tool_search_web in discovery_tools.
    """
    return tool_search_web(
        query=query,
        search_depth=search_depth,
        max_results=max_results,
        progress_callback=progress_callback,
        check_cancellation_fn=check_cancellation,
        sleep_fn=interruptible_sleep,
    )


def run_phase(
    phase_name: str,
    phase_number: int,
    system_prompt: str,
    user_prompt: str,
    max_iterations: int,
    search_depth: str,        # "basic" or "advanced"
    max_results: int,         # 5 or 7
    temperature: float = 0.15,
    progress_callback: Optional[Callable[[str], None]] = None,
    candidate_ledger: Optional[dict] = None,
) -> tuple[str, list[DiscoverySearch]]:
    """
    Runs a single research phase with a fresh context window and multi-tool access.
    Supports search_web, resolve_ticker, get_stock_financials, get_quality_scorecard.
    Accumulates verified findings in candidate_ledger and streams progress.
    Returns the final summary text and a list of searches performed.
    """
    client = get_client()
    if not client:
        raise ValueError("Gemini API key is not configured.")

    if progress_callback:
        progress_callback(f"━━━ Phase {phase_number}/5: {phase_name} ━━━")

    if candidate_ledger is None:
        candidate_ledger = {}

    # Fresh context window for this phase
    contents = [user_prompt]
    searches_performed = []

    # Multi-tool definition for Gemini (search_web, resolve_ticker, get_stock_financials, get_quality_scorecard)
    gemini_tools = get_discovery_gemini_tools()

    iteration = 0
    final_text = ""

    # Primary key for research phases is Key 1 (GEMINI_API_KEY_1)
    primary_key_num = 1
    backup_key_num = 2

    while iteration < max_iterations:
        check_cancellation()
        iteration += 1
        logger.info("Discovery Phase '%s' - Iteration %d/%d", phase_name, iteration, max_iterations)
        
        primary_key_num = get_role_key("research")
        backup_key_num = 2 if primary_key_num == 1 else 1
        current_key_num = primary_key_num
        if is_role_key_exhausted("research", current_key_num):
            current_key_num = backup_key_num

        client = get_client(key_num=current_key_num)
        if not client:
            raise ValueError(f"Gemini API Key {current_key_num} is not configured.")

        gemini_attempt = 0
        gemini_max_retries = 6  # 3 attempts per key x 2 keys

        response = None
        
        while True:
            check_cancellation()
            try:
                # Enforce rate limit (12 calls per minute) before calling Gemini API
                _wait_for_gemini_rate_limit(progress_callback)

                # Increment Gemini call count
                increment_gemini()

                # Phases 1-4 output plain text summaries with multi-tool function calling
                response = client.models.generate_content(
                    model=AI_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        tools=[gemini_tools],
                        thinking_config=types.ThinkingConfig(thinking_budget=-1)
                    )
                )
                break
            except Exception as e:
                if isinstance(e, DiscoveryCancelledException):
                    raise
                gemini_attempt += 1
                if gemini_attempt >= gemini_max_retries:
                    logger.error("Gemini API Error in phase '%s' after %d retries across API keys: %s", phase_name, gemini_max_retries, e)
                    err_msg = e.message if hasattr(e, 'message') else str(e)
                    raise Exception(f"Gemini API error during {phase_name} after retries: {err_msg}")
                
                is_429 = _is_quota_or_rate_limit_error(e)
                has_secondary = get_gemini_key(backup_key_num) != get_gemini_key(primary_key_num)
                secondary_available = has_secondary and not is_role_key_exhausted("research", backup_key_num)

                # If 429 RESOURCE_EXHAUSTED OR 3 retries hit, failover immediately to secondary key & mark primary exhausted for research
                if (is_429 or gemini_attempt == 3) and secondary_available and current_key_num == primary_key_num:
                    mark_role_key_exhausted("research", primary_key_num, reason=f"Research Key {primary_key_num} {'hit 429 RESOURCE_EXHAUSTED' if is_429 else 'failed 3 times'}")
                    current_key_num = backup_key_num
                    client = get_client(key_num=current_key_num)
                    log_msg = f"⚠️ Gemini Key {primary_key_num} {'quota exhausted (429)' if is_429 else 'failed 3 times'} ({str(e)[:60]}). Switching Research to Key {backup_key_num} for this run!"
                    logger.warning(log_msg)
                    if progress_callback:
                        progress_callback(log_msg)
                else:
                    attempt_in_key = gemini_attempt if gemini_attempt <= 3 else (gemini_attempt - 3)
                    wait_secs = 3 * attempt_in_key
                    logger.warning("Gemini API Error (Attempt %d/%d) on Key %d in phase '%s': %s. Retrying in %ds...", 
                                   gemini_attempt, gemini_max_retries, current_key_num, phase_name, e, wait_secs)
                    if progress_callback:
                        progress_callback(f"⚠️ Gemini error (Key {current_key_num}): {str(e)[:60]}... Retrying in {wait_secs}s...")
                    interruptible_sleep(wait_secs)

        # Check if model wants to call a tool
        if response.function_calls:
            contents.append(response.candidates[0].content)
            response_parts = []
            
            for call in response.function_calls:
                tool_name = call.name
                tool_args = dict(call.args) if call.args else {}
                logger.info("[%s] Agent requested tool '%s' with args: %s", phase_name, tool_name, tool_args)

                tool_res, log_msg, urls = execute_discovery_tool(
                    name=tool_name,
                    args=tool_args,
                    candidate_ledger=candidate_ledger,
                    search_depth=search_depth,
                    max_results=max_results,
                    progress_callback=progress_callback,
                    check_cancellation_fn=check_cancellation,
                    sleep_fn=interruptible_sleep,
                )

                if tool_name == "search_web":
                    query = tool_args.get("query", "")
                    search_text = tool_res.get("result", "") if isinstance(tool_res, dict) else str(tool_res)
                    searches_performed.append(
                        DiscoverySearch(
                            query=query,
                            findings=search_text[:1000] + ("..." if len(search_text) > 1000 else ""),
                            sources=urls,
                            phase=phase_name
                        )
                    )
                elif tool_name == "resolve_ticker":
                    c_name = tool_args.get("company_name", "")
                    t_sym = tool_res.get("ticker") if isinstance(tool_res, dict) else None
                    exch = tool_res.get("exchange", "NSE") if isinstance(tool_res, dict) else ""
                    found_text = f"Resolved '{c_name}' -> '{t_sym}' ({exch})" if t_sym else f"Company '{c_name}' unlisted or not found on NSE/BSE"
                    searches_performed.append(
                        DiscoverySearch(
                            query=f"🏷️ resolve_ticker: {c_name}",
                            findings=found_text,
                            sources=["NSE/BSE Master Database"],
                            phase=phase_name
                        )
                    )
                elif tool_name == "get_stock_financials":
                    t_sym = tool_args.get("ticker", "")
                    if isinstance(tool_res, dict) and "audited_financials_inr_cr" in tool_res:
                        fin = tool_res["audited_financials_inr_cr"]
                        ratios = tool_res.get("key_ratios", {})
                        fin_text = (
                            f"Audited Financials for {t_sym}:\n"
                            f"• Revenue (₹ Cr): {fin.get('revenue_history', {})}\n"
                            f"• Operating Margins: {fin.get('operating_margin_history', {})}\n"
                            f"• Net Income (₹ Cr): {fin.get('net_income_history', {})}\n"
                            f"• Free Cash Flow (₹ Cr): {fin.get('free_cashflow_history', {})}\n"
                            f"• Total Debt (₹ Cr): {fin.get('total_debt_history', {})}\n"
                            f"• ROIC: {ratios.get('latest_roic_pct')}%, Debt/Equity: {ratios.get('debt_to_equity')}"
                        )
                    else:
                        fin_text = f"Financial statements fetch for {t_sym}: {str(tool_res)[:500]}"
                    searches_performed.append(
                        DiscoverySearch(
                            query=f"📊 get_stock_financials: {t_sym}",
                            findings=fin_text,
                            sources=["Audited Annual Financials"],
                            phase=phase_name
                        )
                    )
                elif tool_name == "get_quality_scorecard":
                    t_sym = tool_args.get("ticker", "")
                    if isinstance(tool_res, dict) and "quality_score_pct" in tool_res:
                        val = tool_res.get("valuation", {})
                        sc_text = (
                            f"StockLens Quality Scorecard for {t_sym}:\n"
                            f"• Quality Score: {tool_res.get('quality_score_pct')}/100 ({tool_res.get('conviction')})\n"
                            f"• Graham Number: ₹{val.get('graham_number')}, Margin of Safety: {val.get('margin_of_safety_pct')}%\n"
                            f"• DCF Bear Value: ₹{val.get('dcf_bear')}, DCF Base Value: ₹{val.get('dcf_base')}"
                        )
                    else:
                        sc_text = f"Quality scorecard calculation for {t_sym}: {str(tool_res)[:500]}"
                    searches_performed.append(
                        DiscoverySearch(
                            query=f"📈 get_quality_scorecard: {t_sym}",
                            findings=sc_text,
                            sources=["StockLens Valuation Engine"],
                            phase=phase_name
                        )
                    )

                # Build function response part
                part = types.Part.from_function_response(
                    name=call.name,
                    response={"result": tool_res} if not isinstance(tool_res, dict) else tool_res
                )
                response_parts.append(part)
            
            # Feed tool responses back to the model as user role
            contents.append(types.Content(role="user", parts=response_parts))
        else:
            final_text = response.text
            break

    if not final_text:
        # Fallback if loop ended or response has no text
        if response.candidates and response.candidates[0].content.parts:
            final_text = response.candidates[0].content.parts[0].text or ""
        if not final_text:
            raise Exception(f"Phase '{phase_name}' completed without returning any summary text.")

    if progress_callback:
        progress_callback(f"Phase {phase_number} complete ({len(searches_performed)} searches).")

    return final_text, searches_performed


def get_groq_client():
    """Returns a Groq client using OpenAI-compatible SDK."""
    from openai import OpenAI
    if not GROQ_API_KEY:
        return None
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
    )

GROQ_MODEL = "llama-3.3-70b-versatile"


def run_evaluator(
    phase_name: str,
    phase_number: int,
    phase_output: str,
    search_count: int,
    strategy_id: str,
    strategy_name: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """Evaluates the output of a research phase for coverage and depth using EVALUATOR_MODEL, with fallback to AI_MODEL."""
    checklist = STRATEGY_COVERAGE_CHECKLISTS.get(strategy_id, "- [ ] Comprehensive coverage of the strategy objective")

    prompt = EVALUATOR_PROMPT.format(
        strategy_name=strategy_name,
        phase_name=phase_name,
        phase_number=phase_number,
        coverage_checklist=checklist,
        phase_output=phase_output,
        search_count=search_count,
    )

    if progress_callback:
        progress_callback(f"[Evaluator] Assessing Phase {phase_number} coverage and depth...")

    primary_key_num = get_run_primary_key()
    backup_key_num = 2 if primary_key_num == 1 else 1
    
    # Try models in order: EVALUATOR_MODEL (if not exhausted) then AI_MODEL
    models_to_try = []
    if not is_model_exhausted(EVALUATOR_MODEL):
        models_to_try.append(EVALUATOR_MODEL)
    if AI_MODEL != EVALUATOR_MODEL and AI_MODEL not in models_to_try:
        models_to_try.append(AI_MODEL)
    elif not models_to_try:
        models_to_try.append(AI_MODEL)

    response_text = None

    for target_model in models_to_try:
        primary_key_num = get_role_key("evaluator")
        backup_key_num = 2 if primary_key_num == 1 else 1
        current_key_num = primary_key_num
        if is_role_key_exhausted("evaluator", current_key_num):
            current_key_num = backup_key_num

        client = get_client(key_num=current_key_num)
        if not client:
            continue

        gemini_attempt = 0
        gemini_max_retries = 6  # 3 attempts per key x 2 keys

        while gemini_attempt < gemini_max_retries:
            check_cancellation()
            try:
                _wait_for_gemini_rate_limit(progress_callback)
                increment_gemini()

                response = client.models.generate_content(
                    model=target_model,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        system_instruction="You are a research quality evaluator. Return only valid JSON matching the schema.",
                        response_mime_type="application/json",
                        temperature=0.1,
                        thinking_config=types.ThinkingConfig(thinking_budget=-1)
                    )
                )
                response_text = response.text
                break
            except Exception as e:
                if isinstance(e, DiscoveryCancelledException):
                    raise
                gemini_attempt += 1
                is_429 = _is_quota_or_rate_limit_error(e)
                has_secondary = get_gemini_key(backup_key_num) != get_gemini_key(primary_key_num)
                secondary_available = has_secondary and not is_role_key_exhausted("evaluator", backup_key_num)
                
                # If 429 RESOURCE_EXHAUSTED OR 3 retries hit, failover for Evaluator role without affecting Research
                if (is_429 or gemini_attempt == 3) and secondary_available and current_key_num == primary_key_num:
                    mark_role_key_exhausted("evaluator", primary_key_num, reason=f"Evaluator Key {primary_key_num} {'hit 429 RESOURCE_EXHAUSTED' if is_429 else 'failed 3 times'}")
                    current_key_num = backup_key_num
                    client = get_client(key_num=current_key_num)
                    log_msg = f"⚠️ Gemini Key {primary_key_num} {'quota exhausted (429)' if is_429 else 'failed 3 times'} on Evaluator ({str(e)[:60]}). Switching Evaluator to Key {backup_key_num}!"
                    logger.warning(log_msg)
                    if progress_callback:
                        progress_callback(log_msg)
                else:
                    attempt_in_key = gemini_attempt if gemini_attempt <= 3 else (gemini_attempt - 3)
                    wait_secs = 3 * attempt_in_key
                    logger.warning("Gemini API Error (Attempt %d/%d) on Key %d with %s: %s. Retrying in %ds...",
                                   gemini_attempt, gemini_max_retries, current_key_num, target_model, e, wait_secs)
                    if progress_callback:
                        progress_callback(f"⚠️ Evaluator error ({target_model}): {str(e)[:60]}... Retrying in {wait_secs}s...")
                    interruptible_sleep(wait_secs)

        if response_text:
            break
        else:
            mark_model_exhausted(target_model, f"Failed across all API keys during {phase_name} evaluation")
            fallback_msg = f"⚠️ Model '{target_model}' permanently locked to fallback '{AI_MODEL}' for remaining phases."
            logger.warning(fallback_msg)
            if progress_callback:
                progress_callback(fallback_msg)

    if not response_text:
        logger.error("Evaluator failed on all models and keys. Using safe default termination response to allow research to proceed.")
        return {"should_continue": False, "coverage_score": 85, "reasoning_depth_score": 85, "termination_reason": "Evaluator safe fallback due to temporary model 503 high demand spike"}

    try:
        result = _clean_and_parse_json(response_text)
        logger.info(
            "Evaluation for %s - Coverage: %d/100, Depth: %d/100, should_continue: %s, reason: %s",
            phase_name,
            result.get("coverage_score", 0),
            result.get("reasoning_depth_score", 0),
            result.get("should_continue", False),
            result.get("termination_reason", "N/A")
        )
        if progress_callback:
            progress_callback(
                f"📊 Evaluation: Coverage {result.get('coverage_score', 0)}/100 | "
                f"Reasoning {result.get('reasoning_depth_score', 0)}/100 | "
                f"Continue: {result.get('should_continue', False)} | "
                f"Reason: {result.get('termination_reason', 'N/A')}"
            )
        return result
    except Exception as e:
        logger.error("Failed to parse evaluator response as JSON: %s\nRaw: %s", e, response_text)
        return {"should_continue": False, "coverage_score": 85, "reasoning_depth_score": 85, "termination_reason": "Safe fallback on JSON parse failure"}


def run_synthesis(
    system_prompt: str,
    user_prompt: str,
    response_schema: Any,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Runs the final synthesis phase (Phase 5) using EVALUATOR_MODEL, with fallback to AI_MODEL.
    Enforces the response_schema and JSON mime type.
    """
    check_cancellation()
    if progress_callback:
        progress_callback("━━━ Phase 5/5: Synthesis & Self-Critique ━━━")
        progress_callback("[Synthesis] Analyzing accumulated evidence...")

    primary_key_num = get_role_key("synthesis")
    backup_key_num = 2 if primary_key_num == 1 else 1

    # Try models in order: EVALUATOR_MODEL (if not exhausted) then AI_MODEL
    models_to_try = []
    if not is_model_exhausted(EVALUATOR_MODEL):
        models_to_try.append(EVALUATOR_MODEL)
    if AI_MODEL != EVALUATOR_MODEL and AI_MODEL not in models_to_try:
        models_to_try.append(AI_MODEL)
    elif not models_to_try:
        models_to_try.append(AI_MODEL)

    response_text = None

    for target_model in models_to_try:
        check_cancellation()
        primary_key_num = get_role_key("synthesis")
        backup_key_num = 2 if primary_key_num == 1 else 1
        current_key_num = primary_key_num
        if is_role_key_exhausted("synthesis", current_key_num):
            current_key_num = backup_key_num

        client = get_client(key_num=current_key_num)
        if not client:
            continue

        gemini_attempt = 0
        gemini_max_retries = 6  # 3 attempts per key x 2 keys

        while gemini_attempt < gemini_max_retries:
            check_cancellation()
            try:
                _wait_for_gemini_rate_limit(progress_callback)
                increment_gemini()

                response = client.models.generate_content(
                    model=target_model,
                    contents=[user_prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.15,
                        max_output_tokens=8192
                    )
                )
                response_text = response.text
                break
            except Exception as e:
                if isinstance(e, DiscoveryCancelledException):
                    raise
                gemini_attempt += 1
                is_429 = _is_quota_or_rate_limit_error(e)
                has_secondary = get_gemini_key(backup_key_num) != get_gemini_key(primary_key_num)
                secondary_available = has_secondary and not is_role_key_exhausted("synthesis", backup_key_num)

                # If 429 RESOURCE_EXHAUSTED OR 3 retries hit, failover for Synthesis role
                if (is_429 or gemini_attempt == 3) and secondary_available and current_key_num == primary_key_num:
                    mark_role_key_exhausted("synthesis", primary_key_num, reason=f"Synthesis Key {primary_key_num} {'hit 429 RESOURCE_EXHAUSTED' if is_429 else 'failed 3 times'}")
                    current_key_num = backup_key_num
                    client = get_client(key_num=current_key_num)
                    log_msg = f"⚠️ Gemini Key {primary_key_num} {'quota exhausted (429)' if is_429 else 'failed 3 times'} on Synthesis ({str(e)[:60]}). Switching Synthesis to Key {backup_key_num}!"
                    logger.warning(log_msg)
                    if progress_callback:
                        progress_callback(log_msg)
                else:
                    attempt_in_key = gemini_attempt if gemini_attempt <= 3 else (gemini_attempt - 3)
                    wait_secs = 3 * attempt_in_key
                    logger.warning("Gemini API Error (Attempt %d/%d) on Key %d with %s: %s. Retrying in %ds...", 
                                   gemini_attempt, gemini_max_retries, current_key_num, target_model, e, wait_secs)
                    if progress_callback:
                        progress_callback(f"⚠️ Synthesis error ({target_model}): {str(e)[:60]}... Retrying in {wait_secs}s...")
                    interruptible_sleep(wait_secs)

        if response_text:
            break
        else:
            mark_model_exhausted(target_model, "Failed across all API keys during Synthesis")
            fallback_msg = f"⚠️ Synthesis model '{target_model}' permanently locked to fallback '{AI_MODEL}'."
            logger.warning(fallback_msg)
            if progress_callback:
                progress_callback(fallback_msg)

    if not response_text:
        raise Exception("Synthesis completed without returning any response text after retries across models and keys.")

    return response_text


def _get_pending_filepath(strategy_id: str, context: Optional[str] = None) -> str:
    """Returns safe path for pending discovery state keyed by strategy and context."""
    from security_utils import safe_join
    if context and isinstance(context, str) and context.strip():
        safe_ctx = re.sub(r'[^a-zA-Z0-9_-]', '_', context.strip().upper())[:32]
        filename = f"pending_{strategy_id}_{safe_ctx}.json"
    else:
        filename = f"pending_{strategy_id}.json"
    return safe_join(DISCOVERY_DIR, filename)


def save_pending_discovery(
    strategy_id: str,
    context: str,
    current_phase: int,
    phase1_text: Optional[str] = None,
    p1_searches: Optional[list] = None,
    phase2_text: Optional[str] = None,
    p2_searches: Optional[list] = None,
    phase3_text: Optional[str] = None,
    p3_searches: Optional[list] = None,
    phase4_text: Optional[str] = None,
    p4_searches: Optional[list] = None,
    searches_performed: Optional[list] = None,
    candidate_ledger: Optional[dict] = None,
):
    """Saves the intermediate state of an active discovery strategy run to disk."""
    pending_file = _get_pending_filepath(strategy_id, context)
    try:
        def serialize_searches(searches):
            if not searches:
                return []
            res = []
            for s in searches:
                if isinstance(s, dict):
                    res.append(s)
                elif hasattr(s, "model_dump"):
                    res.append(s.model_dump())
                else:
                    res.append(s.dict())
            return res

        data = {
            "strategy_id": strategy_id,
            "context": context,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": current_phase,
            "phase1_text": phase1_text,
            "p1_searches": serialize_searches(p1_searches),
            "phase2_text": phase2_text,
            "p2_searches": serialize_searches(p2_searches),
            "phase3_text": phase3_text,
            "p3_searches": serialize_searches(p3_searches),
            "phase4_text": phase4_text,
            "p4_searches": serialize_searches(p4_searches),
            "searches_performed": serialize_searches(searches_performed),
            "candidate_ledger": candidate_ledger or {}
        }
        from storage import atomic_write_json
        atomic_write_json(pending_file, data)
        logger.info("Saved pending research state for strategy '%s' (%s) at phase %d", strategy_id, context or "global", current_phase)
    except Exception as e:
        logger.error("Failed to save pending discovery state for strategy %s: %s", strategy_id, e)


def delete_pending_discovery(strategy_id: str, context: Optional[str] = None):
    """Removes the pending research state file for a strategy upon completion."""
    pending_file = _get_pending_filepath(strategy_id, context)
    if os.path.exists(pending_file):
        try:
            os.remove(pending_file)
            logger.info("Deleted pending research state for strategy '%s' (%s)", strategy_id, context or "global")
        except Exception as e:
            logger.error("Failed to delete pending discovery state for strategy %s: %s", strategy_id, e)


def run_discovery_stream(
    strategy_id: str,
    context: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> DiscoveryMeta:
    """
    Run the 5-phase agentic deep research pipeline with live session resumption support.
    Accumulates evidence from each phase and synthesizes the final JSON output.
    """
    reset_cancellation()
    reset_run_api_keys()
    client = get_client(key_num=get_run_primary_key())
    if not client:
        raise ValueError("Gemini API key is not configured. Add GEMINI_API_KEY to your .env file.")

    # 1. Resolve strategy
    strategy = next((s for s in DISCOVERY_STRATEGIES if s["id"] == strategy_id), None)
    if not strategy:
        raise ValueError(f"Unknown strategy ID: {strategy_id}")

    context_str = context or ""
    # Strategy-specific template prompt incorporating context
    strategy_objective = strategy["prompt_template"].format(context=context_str)

    # 2. Check for active/pending run for this strategy_id and context
    pending_file = _get_pending_filepath(strategy_id, context_str)
    pending_data = None
    
    if os.path.exists(pending_file):
        try:
            with open(pending_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check context and age (24 hours)
            context_norm_curr = context_str.strip().lower()
            context_norm_saved = (data.get("context") or "").strip().lower()
            
            updated_at_str = data.get("updated_at")
            is_recent = False
            if updated_at_str:
                updated_at = datetime.fromisoformat(updated_at_str)
                age = datetime.now(timezone.utc) - updated_at
                is_recent = age.total_seconds() < 24 * 3600
                
            if context_norm_curr == context_norm_saved and is_recent:
                pending_data = data
                if progress_callback:
                    progress_callback(
                        f"⏳ Found incomplete run for strategy '{strategy['name']}' from {updated_at_str}. "
                        f"Resuming from Phase {data.get('current_phase', 1)}..."
                    )
        except Exception as e:
            logger.warning("Failed to check/load pending discovery: %s", e)

    # Initialize variables based on whether we are resuming or starting fresh
    if pending_data:
        phase1_text = pending_data.get("phase1_text")
        p1_searches = [DiscoverySearch(**s) for s in pending_data.get("p1_searches") or []]
        
        phase2_text = pending_data.get("phase2_text")
        p2_searches = [DiscoverySearch(**s) for s in pending_data.get("p2_searches") or []]
        
        phase3_text = pending_data.get("phase3_text")
        p3_searches = [DiscoverySearch(**s) for s in pending_data.get("p3_searches") or []]
        
        phase4_text = pending_data.get("phase4_text")
        p4_searches = [DiscoverySearch(**s) for s in pending_data.get("p4_searches") or []]
        
        searches_performed = [DiscoverySearch(**s) for s in pending_data.get("searches_performed") or []]
        candidate_ledger = pending_data.get("candidate_ledger", {}) or {}
        start_phase = pending_data.get("current_phase", 1)
        response_text = ""
    else:
        phase1_text = None
        p1_searches = []
        phase2_text = None
        p2_searches = []
        phase3_text = None
        p3_searches = []
        phase4_text = None
        p4_searches = []
        searches_performed = []
        candidate_ledger = {}
        start_phase = 1
        response_text = ""

    # --- PHASE 1: LANDSCAPE SCAN ---
    check_cancellation()
    if start_phase <= 1:
        if not phase1_text:
            phase1_prompt = PHASE_1_LANDSCAPE_PROMPT.format(
                strategy_objective=strategy_objective,
                max_iterations=18
            )
            phase1_text, p1_searches = run_phase(
                phase_name="Landscape Scan",
                phase_number=1,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=phase1_prompt,
                max_iterations=18,
                search_depth="basic",
                max_results=5,
                temperature=0.45,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

        # Depth Loop
        for depth_loop in range(3):
            eval_result = run_evaluator(
                phase_name="Landscape Scan",
                phase_number=1,
                phase_output=phase1_text,
                search_count=len(p1_searches),
                strategy_id=strategy_id,
                strategy_name=strategy["name"],
                progress_callback=progress_callback,
            )

            if not eval_result.get("should_continue", False):
                break

            already_searched = "\n".join(f"- {s.query}" for s in p1_searches)

            continuation_prompt = DEPTH_LOOP_CONTINUATION_PROMPT.format(
                loop_iteration=depth_loop + 1,
                max_loops=3,
                strategy_objective=strategy_objective,
                previous_output=phase1_text,
                coverage_score=eval_result.get("coverage_score", 0),
                reasoning_score=eval_result.get("reasoning_depth_score", 0),
                alternative_angle=eval_result.get("alternative_analyst_angle") or "None identified.",
                gaps="\n".join(
                    f"- [{g.get('availability', 'UNKNOWN')}] {g.get('topic', '')}" if isinstance(g, dict) else f"- {g}"
                    for g in eval_result.get("gaps", [])
                ) if isinstance(eval_result.get("gaps"), list) else "None specified.",
                search_queries="\n".join(f"- {q}" for q in eval_result.get("search_queries", []) if isinstance(q, str)) if isinstance(eval_result.get("search_queries"), list) else "None requested.",
                reasoning_prompts="\n".join(f"- {r}" for r in eval_result.get("reasoning_prompts", []) if isinstance(r, str)) if isinstance(eval_result.get("reasoning_prompts"), list) else "None specified.",
                already_searched=already_searched,
                max_iterations=10,
            )

            continuation_text, continuation_searches = run_phase(
                phase_name=f"Landscape Scan (Depth {depth_loop + 1})",
                phase_number=1,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=continuation_prompt,
                max_iterations=10,
                search_depth="advanced",
                max_results=5,
                temperature=0.45,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

            phase1_text = continuation_text
            p1_searches.extend(continuation_searches)

            save_pending_discovery(
                strategy_id=strategy_id,
                context=context_str,
                current_phase=1,
                phase1_text=phase1_text,
                p1_searches=p1_searches,
                searches_performed=searches_performed + p1_searches,
                candidate_ledger=candidate_ledger
            )

        searches_performed.extend(p1_searches)
        save_pending_discovery(
            strategy_id=strategy_id,
            context=context_str,
            current_phase=2,
            phase1_text=phase1_text,
            p1_searches=p1_searches,
            searches_performed=searches_performed,
            candidate_ledger=candidate_ledger
        )

    # --- PHASE 2: COURSE CORRECTION ---
    if start_phase <= 2:
        check_cancellation()
        if progress_callback and start_phase == 2:
            progress_callback("🔄 Resuming: Loading Phase 1 results from live storage...")

        if not phase2_text:
            phase2_prompt = PHASE_2_CORRECTION_PROMPT.format(
                strategy_objective=strategy_objective,
                phase1_evidence=phase1_text,
                max_iterations=10
            )
            phase2_text, p2_searches = run_phase(
                phase_name="Course Correction",
                phase_number=2,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=phase2_prompt,
                max_iterations=10,
                search_depth="basic",
                max_results=5,
                temperature=0.25,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

        # Depth Loop
        for depth_loop in range(3):
            check_cancellation()
            eval_result = run_evaluator(
                phase_name="Course Correction",
                phase_number=2,
                phase_output=phase2_text,
                search_count=len(p2_searches),
                strategy_id=strategy_id,
                strategy_name=strategy["name"],
                progress_callback=progress_callback,
            )

            if not eval_result.get("should_continue", False):
                break

            already_searched = "\n".join(f"- {s.query}" for s in p2_searches)

            continuation_prompt = DEPTH_LOOP_CONTINUATION_PROMPT.format(
                loop_iteration=depth_loop + 1,
                max_loops=3,
                strategy_objective=strategy_objective,
                previous_output=phase2_text,
                coverage_score=eval_result.get("coverage_score", 0),
                reasoning_score=eval_result.get("reasoning_depth_score", 0),
                alternative_angle=eval_result.get("alternative_analyst_angle") or "None identified.",
                gaps="\n".join(
                    f"- [{g.get('availability', 'UNKNOWN')}] {g.get('topic', '')}" if isinstance(g, dict) else f"- {g}"
                    for g in eval_result.get("gaps", [])
                ) if isinstance(eval_result.get("gaps"), list) else "None specified.",
                search_queries="\n".join(f"- {q}" for q in eval_result.get("search_queries", []) if isinstance(q, str)) if isinstance(eval_result.get("search_queries"), list) else "None requested.",
                reasoning_prompts="\n".join(f"- {r}" for r in eval_result.get("reasoning_prompts", []) if isinstance(r, str)) if isinstance(eval_result.get("reasoning_prompts"), list) else "None specified.",
                already_searched=already_searched,
                max_iterations=10,
            )

            continuation_text, continuation_searches = run_phase(
                phase_name=f"Course Correction (Depth {depth_loop + 1})",
                phase_number=2,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=continuation_prompt,
                max_iterations=10,
                search_depth="advanced",
                max_results=5,
                temperature=0.25,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

            phase2_text = continuation_text
            p2_searches.extend(continuation_searches)

            save_pending_discovery(
                strategy_id=strategy_id,
                context=context_str,
                current_phase=2,
                phase1_text=phase1_text,
                p1_searches=p1_searches,
                phase2_text=phase2_text,
                p2_searches=p2_searches,
                searches_performed=searches_performed + p2_searches,
                candidate_ledger=candidate_ledger
            )

        searches_performed.extend(p2_searches)
        save_pending_discovery(
            strategy_id=strategy_id,
            context=context_str,
            current_phase=3,
            phase1_text=phase1_text,
            p1_searches=p1_searches,
            phase2_text=phase2_text,
            p2_searches=p2_searches,
            searches_performed=searches_performed,
            candidate_ledger=candidate_ledger
        )

    # --- PHASE 3: CANDIDATE DEEP DIVE ---
    if start_phase <= 3:
        check_cancellation()
        if progress_callback and start_phase == 3:
            progress_callback("🔄 Resuming: Loading Phase 1 & 2 results from live storage...")

        if not phase3_text:
            phase3_prompt = PHASE_3_DEEPDIVE_PROMPT.format(
                strategy_objective=strategy_objective,
                evidence=phase1_text + "\n\n" + phase2_text,
                max_iterations=22
            )
            phase3_text, p3_searches = run_phase(
                phase_name="Candidate Deep Dive",
                phase_number=3,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=phase3_prompt,
                max_iterations=22,
                search_depth="advanced",
                max_results=7,
                temperature=0.15,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

        # Depth Loop
        for depth_loop in range(3):
            check_cancellation()
            eval_result = run_evaluator(
                phase_name="Candidate Deep Dive",
                phase_number=3,
                phase_output=phase3_text,
                search_count=len(p3_searches),
                strategy_id=strategy_id,
                strategy_name=strategy["name"],
                progress_callback=progress_callback,
            )

            if not eval_result.get("should_continue", False):
                break

            already_searched = "\n".join(f"- {s.query}" for s in p3_searches)

            continuation_prompt = DEPTH_LOOP_CONTINUATION_PROMPT.format(
                loop_iteration=depth_loop + 1,
                max_loops=3,
                strategy_objective=strategy_objective,
                previous_output=phase3_text,
                coverage_score=eval_result.get("coverage_score", 0),
                reasoning_score=eval_result.get("reasoning_depth_score", 0),
                alternative_angle=eval_result.get("alternative_analyst_angle") or "None identified.",
                gaps="\n".join(
                    f"- [{g.get('availability', 'UNKNOWN')}] {g.get('topic', '')}" if isinstance(g, dict) else f"- {g}"
                    for g in eval_result.get("gaps", [])
                ) if isinstance(eval_result.get("gaps"), list) else "None specified.",
                search_queries="\n".join(f"- {q}" for q in eval_result.get("search_queries", []) if isinstance(q, str)) if isinstance(eval_result.get("search_queries"), list) else "None requested.",
                reasoning_prompts="\n".join(f"- {r}" for r in eval_result.get("reasoning_prompts", []) if isinstance(r, str)) if isinstance(eval_result.get("reasoning_prompts"), list) else "None specified.",
                already_searched=already_searched,
                max_iterations=10,
            )

            continuation_text, continuation_searches = run_phase(
                phase_name=f"Candidate Deep Dive (Depth {depth_loop + 1})",
                phase_number=3,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=continuation_prompt,
                max_iterations=10,
                search_depth="advanced",
                max_results=5,
                temperature=0.15,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

            phase3_text = continuation_text
            p3_searches.extend(continuation_searches)

            save_pending_discovery(
                strategy_id=strategy_id,
                context=context_str,
                current_phase=3,
                phase1_text=phase1_text,
                p1_searches=p1_searches,
                phase2_text=phase2_text,
                p2_searches=p2_searches,
                phase3_text=phase3_text,
                p3_searches=p3_searches,
                searches_performed=searches_performed + p3_searches,
                candidate_ledger=candidate_ledger
            )

        searches_performed.extend(p3_searches)
        save_pending_discovery(
            strategy_id=strategy_id,
            context=context_str,
            current_phase=4,
            phase1_text=phase1_text,
            p1_searches=p1_searches,
            phase2_text=phase2_text,
            p2_searches=p2_searches,
            phase3_text=phase3_text,
            p3_searches=p3_searches,
            searches_performed=searches_performed,
            candidate_ledger=candidate_ledger
        )

    # --- PHASE 4: CROSS-VERIFICATION ---
    check_cancellation()
    all_intermediate_evidence = (
        f"--- PHASE 1: LANDSCAPE SCAN ---\n{phase1_text}\n\n"
        f"--- PHASE 2: COURSE CORRECTION ---\n{phase2_text}\n\n"
        f"--- PHASE 3: CANDIDATE DEEP DIVE ---\n{phase3_text}"
    )

    if start_phase <= 4:
        check_cancellation()
        if progress_callback and start_phase == 4:
            progress_callback("🔄 Resuming: Loading Phase 1, 2 & 3 results from live storage...")

        if not phase4_text:
            phase4_prompt = PHASE_4_VERIFICATION_PROMPT.format(
                strategy_objective=strategy_objective,
                evidence=all_intermediate_evidence,
                max_iterations=12
            )
            phase4_text, p4_searches = run_phase(
                phase_name="Cross-Verification",
                phase_number=4,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=phase4_prompt,
                max_iterations=12,
                search_depth="advanced",
                max_results=5,
                temperature=0.10,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

        # Depth Loop
        for depth_loop in range(3):
            check_cancellation()
            eval_result = run_evaluator(
                phase_name="Cross-Verification",
                phase_number=4,
                phase_output=phase4_text,
                search_count=len(p4_searches),
                strategy_id=strategy_id,
                strategy_name=strategy["name"],
                progress_callback=progress_callback,
            )

            if not eval_result.get("should_continue", False):
                break

            already_searched = "\n".join(f"- {s.query}" for s in p4_searches)

            continuation_prompt = DEPTH_LOOP_CONTINUATION_PROMPT.format(
                loop_iteration=depth_loop + 1,
                max_loops=3,
                strategy_objective=strategy_objective,
                previous_output=phase4_text,
                coverage_score=eval_result.get("coverage_score", 0),
                reasoning_score=eval_result.get("reasoning_depth_score", 0),
                alternative_angle=eval_result.get("alternative_analyst_angle") or "None identified.",
                gaps="\n".join(
                    f"- [{g.get('availability', 'UNKNOWN')}] {g.get('topic', '')}" if isinstance(g, dict) else f"- {g}"
                    for g in eval_result.get("gaps", [])
                ) if isinstance(eval_result.get("gaps"), list) else "None specified.",
                search_queries="\n".join(f"- {q}" for q in eval_result.get("search_queries", []) if isinstance(q, str)) if isinstance(eval_result.get("search_queries"), list) else "None requested.",
                reasoning_prompts="\n".join(f"- {r}" for r in eval_result.get("reasoning_prompts", []) if isinstance(r, str)) if isinstance(eval_result.get("reasoning_prompts"), list) else "None specified.",
                already_searched=already_searched,
                max_iterations=10,
            )

            continuation_text, continuation_searches = run_phase(
                phase_name=f"Cross-Verification (Depth {depth_loop + 1})",
                phase_number=4,
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                user_prompt=continuation_prompt,
                max_iterations=10,
                search_depth="advanced",
                max_results=5,
                temperature=0.10,
                progress_callback=progress_callback,
                candidate_ledger=candidate_ledger
            )

            phase4_text = continuation_text
            p4_searches.extend(continuation_searches)

            save_pending_discovery(
                strategy_id=strategy_id,
                context=context_str,
                current_phase=4,
                phase1_text=phase1_text,
                p1_searches=p1_searches,
                phase2_text=phase2_text,
                p2_searches=p2_searches,
                phase3_text=phase3_text,
                p3_searches=p3_searches,
                phase4_text=phase4_text,
                p4_searches=p4_searches,
                searches_performed=searches_performed + p4_searches,
                candidate_ledger=candidate_ledger
            )

        searches_performed.extend(p4_searches)
        save_pending_discovery(
            strategy_id=strategy_id,
            context=context_str,
            current_phase=5,
            phase1_text=phase1_text,
            p1_searches=p1_searches,
            phase2_text=phase2_text,
            p2_searches=p2_searches,
            phase3_text=phase3_text,
            p3_searches=p3_searches,
            phase4_text=phase4_text,
            p4_searches=p4_searches,
            searches_performed=searches_performed,
            candidate_ledger=candidate_ledger
        )

    # --- PHASE 5: SYNTHESIS ---
    if start_phase <= 5:
        if progress_callback and start_phase == 5:
            progress_callback("🔄 Resuming: Loading all intermediate phase results from live storage...")
        
        # Format Candidate Ledger into structured ground-truth evidence
        ledger_text = ""
        if candidate_ledger:
            ledger_blocks = []
            for t_sym, c_data in candidate_ledger.items():
                block = [f"### AUDITED CANDIDATE: {c_data.get('company_name', t_sym)} ({t_sym})"]
                if c_data.get("exchange"):
                    block.append(f"- Exchange: {c_data['exchange']}")
                fin = c_data.get("audited_financials")
                if fin and isinstance(fin, dict) and "audited_financials_inr_cr" in fin:
                    stmt = fin["audited_financials_inr_cr"]
                    ratios = fin.get("key_ratios", {})
                    block.append(f"- Audited Revenue History (₹ Cr): {stmt.get('revenue_history', {})}")
                    block.append(f"- Audited Operating Income (₹ Cr): {stmt.get('operating_income_history', {})}")
                    block.append(f"- Audited Net Income (₹ Cr): {stmt.get('net_income_history', {})}")
                    block.append(f"- Audited Operating Margins: {stmt.get('operating_margin_history', {})}")
                    block.append(f"- Audited Free Cash Flow (₹ Cr): {stmt.get('free_cashflow_history', {})}")
                    block.append(f"- Audited Total Debt (₹ Cr): {stmt.get('total_debt_history', {})}")
                    block.append(f"- Key Ratios: Latest ROIC: {ratios.get('latest_roic_pct')}%, Debt/Equity: {ratios.get('debt_to_equity')}, Current Ratio: {ratios.get('current_ratio')}, PE: {ratios.get('pe_ratio')}")
                sc = c_data.get("quality_scorecard")
                if sc and isinstance(sc, dict):
                    val = sc.get("valuation", {})
                    block.append(f"- StockLens Quality Score: {sc.get('quality_score_pct')}/100 ({sc.get('conviction')})")
                    block.append(f"- Valuation & Margin of Safety: Graham: ₹{val.get('graham_number')}, Margin of Safety: {val.get('margin_of_safety_pct')}%, DCF Bear: ₹{val.get('dcf_bear')}, DCF Base: ₹{val.get('dcf_base')}")
                ledger_blocks.append("\n".join(block))

            ledger_text = (
                "\n\n--- AUDITED CANDIDATE LEDGER (GROUND TRUTH TOOL DATA) ---\n"
                "CRITICAL INSTRUCTION: The following candidates have been verified with audited financial statements and fundamental scorecards. "
                "You MUST use these verified tickers, audited numbers, and quality scores when synthesizing candidate cards:\n\n"
                + "\n\n".join(ledger_blocks)
            )

        full_compiled_evidence = (
            f"{all_intermediate_evidence}\n\n"
            f"--- PHASE 4: CROSS-VERIFICATION ---\n{phase4_text}"
            f"{ledger_text}"
        )
        phase5_prompt = PHASE_5_SYNTHESIS_PROMPT.format(
            strategy_objective=strategy_objective,
            all_evidence=full_compiled_evidence
        )
        
        response_text = run_synthesis(
            system_prompt=SYNTHESIS_SYSTEM_PROMPT,
            user_prompt=phase5_prompt,
            response_schema=DiscoveryResult,
            progress_callback=progress_callback
        )

    # 3. Clean and parse JSON response (with repair for LLM quirks)
    try:
        parsed_data = _clean_and_parse_json(response_text)
    except Exception as e:
        logger.error("Failed to parse JSON response: %s\nRaw text: %s", e, response_text)
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}")

    # Ensure disclaimer is populated
    if "disclaimer" not in parsed_data or not parsed_data["disclaimer"]:
        parsed_data["disclaimer"] = "AI-generated hypotheses. Every candidate requires independent verification."

    # Helper functions for defensive type conversion
    def _stringify_field(val: Any) -> str:
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            return "\n".join(f"**{k}**: {v}" for k, v in val.items())
        if isinstance(val, list):
            return "\n".join(f"- {item}" for item in val)
        return str(val) if val is not None else ""

    def _listify_field(val: Any) -> list[str]:
        if isinstance(val, list):
            return [str(item) for item in val]
        if isinstance(val, str):
            return [val] if val.strip() else []
        if isinstance(val, dict):
            return [f"{k}: {v}" for k, v in val.items()]
        return []

    # Map parsed data to DiscoveryResult Pydantic structure
    candidates = []
    for c in parsed_data.get("candidates", []):
        if not isinstance(c, dict):
            continue
        c_name = _stringify_field(c.get("company_name", ""))
        c_ticker = c.get("ticker") if isinstance(c.get("ticker"), str) else None

        # Cross-reference with candidate ledger to backfill/correct tickers
        if candidate_ledger:
            if not c_ticker:
                for t_sym, l_data in candidate_ledger.items():
                    if l_data.get("company_name", "").lower() == c_name.lower() or c_name.lower() in l_data.get("company_name", "").lower():
                        c_ticker = t_sym
                        break

        candidates.append(
            DiscoveryCandidate(
                company_name=c_name,
                ticker=c_ticker,
                connection_type=_stringify_field(c.get("connection_type", "")),
                confidence=str(c.get("confidence", "medium")).lower(),
                why_now=_stringify_field(c.get("why_now", "")),
                reasoning=_stringify_field(c.get("reasoning", "")),
                self_critique=_stringify_field(c.get("self_critique", "")),
                disproving_evidence=_stringify_field(c.get("disproving_evidence", "")),
                risks=_listify_field(c.get("risks", [])),
                what_to_verify=_listify_field(c.get("what_to_verify", [])),
                sources=_listify_field(c.get("sources", [])),
                confidence_evolution=_listify_field(c.get("confidence_evolution", []))
            )
        )

    discovery_result = DiscoveryResult(
        analysis_summary=_stringify_field(parsed_data.get("analysis_summary", "")),
        candidates=candidates,
        limitations=_listify_field(parsed_data.get("limitations", [])),
        searches_performed=searches_performed,
        disclaimer=parsed_data["disclaimer"],
        phases_completed=5,
        total_search_count=len(searches_performed)
    )

    # 4. Save discovery metadata
    discovery_id = str(uuid.uuid4())
    meta = DiscoveryMeta(
        id=discovery_id,
        strategy_id=strategy_id,
        strategy_name=strategy["name"],
        user_params={"context": context},
        model_name=AI_MODEL,
        created_at=datetime.utcnow().isoformat(),
        result=discovery_result
    )
    
    save_discovery(meta)
    
    # 5. Clean up pending live storage
    delete_pending_discovery(strategy_id, context_str)
    
    return meta


def save_discovery(meta: DiscoveryMeta):
    """Saves a discovery meta object to local disk as JSON atomically."""
    from security_utils import safe_join, validate_uuid
    from storage import atomic_write_json
    try:
        safe_id = validate_uuid(meta.id)
        filepath = safe_join(DISCOVERY_DIR, f"{safe_id}.json")
        # Pydantic v1 & v2 compatibility
        if hasattr(meta, "model_dump"):
            data = meta.model_dump()
        else:
            data = meta.dict()
            
        atomic_write_json(filepath, data)
        logger.info("Discovery %s atomically saved to disk", safe_id)
    except Exception as e:
        logger.error("Failed to save discovery %s: %s", meta.id, e)


def get_saved_discoveries() -> list[DiscoverySummary]:
    """Returns a sorted list of all saved discoveries, ignoring pending files and corrupted items."""
    from security_utils import safe_join
    from storage import safe_read_json
    summaries = []
    if not os.path.exists(DISCOVERY_DIR):
        return summaries

    for filename in os.listdir(DISCOVERY_DIR):
        if not filename.endswith(".json") or filename.startswith("pending_") or filename.startswith("."):
            continue
        
        try:
            filepath = safe_join(DISCOVERY_DIR, filename)
            data = safe_read_json(filepath)
            if not data or not isinstance(data, dict):
                continue
            
            result = data.get("result", {})
            candidates = result.get("candidates", [])
            context = data.get("user_params", {}).get("context", "")
            preview = context[:100] + ("..." if len(context) > 100 else "") if context else "No input context"
            
            summaries.append(
                DiscoverySummary(
                    id=data.get("id", ""),
                    strategy_name=data.get("strategy_name", ""),
                    user_input_preview=preview,
                    candidate_count=len(candidates),
                    created_at=data.get("created_at", "")
                )
            )
        except Exception as e:
            logger.warning("Error reading discovery file %s (skipping): %s", filename, e)

    # Sort by created_at descending
    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def get_discovery(discovery_id: str) -> Optional[DiscoveryMeta]:
    """Loads a specific discovery by ID from disk."""
    from security_utils import safe_join, validate_uuid
    from storage import safe_read_json
    try:
        safe_id = validate_uuid(discovery_id)
        filepath = safe_join(DISCOVERY_DIR, f"{safe_id}.json")
    except ValueError:
        return None

    if not os.path.exists(filepath):
        return None
    try:
        data = safe_read_json(filepath)
        if data and isinstance(data, dict):
            return DiscoveryMeta(**data)
        return None
    except Exception as e:
        logger.error("Failed to parse discovery %s: %s", discovery_id, e)
        return None


def delete_discovery(discovery_id: str, context: Optional[str] = None) -> bool:
    """Deletes a saved discovery file from disk."""
    from security_utils import safe_join, validate_uuid
    try:
        safe_id = validate_uuid(discovery_id)
        filepath = safe_join(DISCOVERY_DIR, f"{safe_id}.json")
    except ValueError:
        return False

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            logger.error("Failed to delete discovery %s: %s", discovery_id, e)
            return False
    return False


# Alias for backward compatibility with route callers
run_discovery_strategy = run_discovery_stream
