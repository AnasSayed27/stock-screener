import os
import json
import time
from datetime import datetime
import shutil
from typing import Any, Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import AI_ENABLED, AI_MODEL, AI_TEMP_DIR, AI_REPORTS_DIR
from models import (
    AIBusinessOverview,
    AIGovernanceReport,
    AIRiskAnalysis,
    AIThesisDraft,
    AIAnswer,
    AIReportMeta,
    AICitation
)
from prompts import (
    SYSTEM_INSTRUCTION,
    BUSINESS_OVERVIEW_PROMPT,
    GOVERNANCE_PROMPT,
    RISK_ANALYSIS_PROMPT,
    THESIS_DRAFT_PROMPT,
    QA_PROMPT
)
from usage_tracker import increment_gemini

# In-memory session store (single-user local app)
# Structure:
# _sessions[ticker] = {
#     "gemini_files": [...],      # list of uploaded file references (google.genai.types.File)
#     "documents_used": [...],    # list of filenames (strings)
#     "history": []               # Q&A history: [{"role": "user" | "model", "text": str}]
# }
_sessions: dict[str, dict] = {}


def get_gemini_key(key_num: int = 1) -> Optional[str]:
    """
    Get Gemini API key 1 or 2 with fallbacks:
    key_num=1: GEMINI_API_KEY_1 or GEMINI_API_KEY
    key_num=2: GEMINI_API_KEY_2 or GEMINI_API_KEY_1 or GEMINI_API_KEY
    """
    key1 = os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY")
    key2 = os.environ.get("GEMINI_API_KEY_2")
    if key_num == 2 and key2:
        return key2
    return key1 or key2


def get_client(key_num: int = 1, api_key: Optional[str] = None) -> Optional[genai.Client]:
    """Initialize and return the Gemini client for a given API key or key number."""
    if not api_key:
        api_key = get_gemini_key(key_num)
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def load_session_from_disk(ticker: str) -> dict:
    from security_utils import safe_join, sanitize_ticker
    safe_t = sanitize_ticker(ticker)
    session_file = safe_join(AI_TEMP_DIR, safe_t, "session.json")
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Reconstruct the session
            # We fetch the file references from Gemini API using the stored file names
            client = get_client()
            gemini_files = []
            if client and data.get("gemini_file_names"):
                for name in data["gemini_file_names"]:
                    try:
                        file_ref = client.files.get(name=name)
                        gemini_files.append(file_ref)
                    except Exception as e:
                        print(f"Error fetching file ref {name} from Gemini: {e}")
            
            return {
                "gemini_files": gemini_files,
                "documents_used": data.get("documents_used", []),
                "history": data.get("history", [])
            }
        except Exception as e:
            print(f"Error loading session from disk for {ticker}: {e}")
            
    return {
        "gemini_files": [],
        "documents_used": [],
        "history": []
    }


def save_session_to_disk(ticker: str, session: dict):
    from security_utils import safe_join, sanitize_ticker
    safe_t = sanitize_ticker(ticker)
    target_dir = safe_join(AI_TEMP_DIR, safe_t)
    os.makedirs(target_dir, exist_ok=True)
    session_file = safe_join(target_dir, "session.json")
    try:
        gemini_file_names = [f.name for f in session.get("gemini_files", [])]
        data = {
            "gemini_file_names": gemini_file_names,
            "documents_used": session.get("documents_used", []),
            "history": session.get("history", [])
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving session to disk for {ticker}: {e}")


def get_session(ticker: str) -> dict:
    """Get or initialize session for a ticker."""
    from security_utils import sanitize_ticker
    safe_t = sanitize_ticker(ticker)
    if safe_t not in _sessions:
        _sessions[safe_t] = load_session_from_disk(safe_t)
    return _sessions[safe_t]


def clear_session(ticker: str, keep_temp_dir: bool = False) -> dict:
    """
    Clears session for a ticker, including deleting files from Gemini Files API
    and removing local temp files. Saved reports are NOT deleted.
    """
    from security_utils import safe_join, sanitize_ticker
    safe_t = sanitize_ticker(ticker)
    session = _sessions.get(safe_t)
    client = get_client()

    if session and client:
        # Delete files from Gemini API to free up storage
        for file_ref in session.get("gemini_files", []):
            try:
                client.files.delete(name=file_ref.name)
            except Exception as e:
                # Log error but don't fail the cleanup
                print(f"Error deleting file {file_ref.name} from Gemini API: {e}")

    # Remove in-memory session
    if safe_t in _sessions:
        del _sessions[safe_t]

    # Delete local temp directory for this ticker
    if not keep_temp_dir:
        temp_dir = safe_join(AI_TEMP_DIR, safe_t)
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error removing temp directory {temp_dir}: {e}")

    return {"cleared": True}


def upload_file_to_gemini(client: genai.Client, file_path: str) -> Any:
    """Uploads a single file to Gemini Files API and polls until ACTIVE."""
    file_ref = client.files.upload(file=file_path)
    
    # Poll state of the uploaded file
    state_str = getattr(file_ref.state, "name", str(file_ref.state))
    max_retries = 30
    retry_count = 0
    
    while state_str == "PROCESSING" and retry_count < max_retries:
        time.sleep(2)
        file_ref = client.files.get(name=file_ref.name)
        state_str = getattr(file_ref.state, "name", str(file_ref.state))
        retry_count += 1
        
    if state_str != "ACTIVE":
        raise Exception(f"File {os.path.basename(file_path)} upload failed with state: {state_str}")
        
    return file_ref


def upload_documents(ticker: str, file_paths: list[str]) -> dict:
    """
    Uploads local files to Gemini Files API and registers them in the ticker's session.
    Appends new files to the session, overwriting files with the same name.
    """
    client = get_client()
    if not client:
        raise ValueError("Gemini API key is not configured. Add GEMINI_API_KEY to your .env file.")

    session = get_session(ticker)

    # Convert existing session files to lists to support mutations
    gemini_files = list(session.get("gemini_files", []))
    documents_used = list(session.get("documents_used", []))

    new_uploads = []

    for path in file_paths:
        if not os.path.exists(path):
            continue
        filename = os.path.basename(path)

        # If a file with the same name already exists in the session, delete its old reference from the Gemini API
        if filename in documents_used:
            idx = documents_used.index(filename)
            old_file_ref = gemini_files[idx]
            try:
                client.files.delete(name=old_file_ref.name)
            except Exception as e:
                print(f"Error deleting replaced file {old_file_ref.name} from Gemini API: {e}")

            # Remove from local lists
            del gemini_files[idx]
            del documents_used[idx]

        try:
            file_ref = upload_file_to_gemini(client, path)
            gemini_files.append(file_ref)
            documents_used.append(filename)
            new_uploads.append(file_ref)
        except Exception as e:
            # Cleanup only newly uploaded files in this partial run
            for ref in new_uploads:
                try:
                    client.files.delete(name=ref.name)
                except:
                    pass
            raise Exception(f"Failed to upload document {filename}: {str(e)}")

    session["gemini_files"] = gemini_files
    session["documents_used"] = documents_used
    save_session_to_disk(ticker, session)

    return {
        "files_uploaded": len(file_paths),
        "file_names": documents_used
    }


def analyze_documents(
    mode: str,
    ticker: str,
    question: str = "",
    context: Optional[dict] = None
) -> dict:
    """
    Analyzes uploaded documents for a ticker based on the mode.
    Modes: "business", "governance", "risks", "thesis", "qa"
    Saves generated reports to disk (except "qa" mode).
    """
    client = get_client()
    if not client:
        raise ValueError("Gemini API key is not configured. Add GEMINI_API_KEY to your .env file.")

    session = get_session(ticker)
    gemini_files = session.get("gemini_files", [])

    # Self-healing: If Gemini files expired (48h lifecycle) but local PDFs exist, re-upload them
    if not gemini_files:
        from security_utils import safe_join, sanitize_ticker
        safe_t = sanitize_ticker(ticker)
        temp_dir = safe_join(AI_TEMP_DIR, safe_t)
        if os.path.exists(temp_dir):
            local_pdfs = [
                safe_join(temp_dir, f)
                for f in os.listdir(temp_dir)
                if f.lower().endswith(".pdf")
            ]
            if local_pdfs:
                try:
                    upload_documents(safe_t, local_pdfs)
                    session = get_session(safe_t)
                    gemini_files = session.get("gemini_files", [])
                except Exception as e:
                    print(f"Failed to auto re-upload expired Gemini files for {safe_t}: {e}")

    if not gemini_files:
        raise ValueError(
            "No active session or uploaded documents found for this stock. "
            "Please upload documents first."
        )

    # 1. Determine Prompt and Response Schema based on Mode
    if mode == "business":
        prompt = BUSINESS_OVERVIEW_PROMPT.format(ticker=ticker)
        schema = AIBusinessOverview
    elif mode == "governance":
        prompt = GOVERNANCE_PROMPT.format(ticker=ticker)
        schema = AIGovernanceReport
    elif mode == "risks":
        prompt = RISK_ANALYSIS_PROMPT.format(ticker=ticker)
        schema = AIRiskAnalysis
    elif mode == "thesis":
        scorecard_context = json.dumps(context or {}, indent=2)
        prompt = THESIS_DRAFT_PROMPT.format(ticker=ticker, scorecard_context=scorecard_context)
        schema = AIThesisDraft
    elif mode == "qa":
        # Format Q&A history into prompt
        history = session.get("history", [])
        history_str = ""
        if history:
            history_str = "\n\nPrevious Q&A conversation history for context:\n"
            for item in history:
                role_label = "User" if item["role"] == "user" else "Assistant"
                history_str += f"{role_label}: {item['text']}\n"
        
        prompt = QA_PROMPT.format(question=question)
        if history_str:
            prompt = history_str + "\n" + prompt
            
        schema = AIAnswer
    else:
        raise ValueError(f"Invalid analysis mode: {mode}")

    # 2. Call Gemini API with retries and exponential backoff
    # Combine file references and the text prompt in the contents list
    contents = list(gemini_files) + [prompt]

    prompt_versions = {
        "business": "business_prompt_v2",
        "governance": "governance_prompt_v2",
        "risks": "risk_prompt_v2",
        "thesis": "thesis_prompt_v2",
        "qa": "qa_prompt_v2"
    }
    prompt_ver = prompt_versions.get(mode, "unknown_version")

    max_retries = 2
    delay = 2.0
    response = None

    for attempt in range(max_retries + 1):
        try:
            increment_gemini()
            response = client.models.generate_content(
                model=AI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1,
                    top_p=0.9,
                    top_k=20,
                    thinking_config=types.ThinkingConfig(thinking_budget=-1)
                )
            )
            break
        except APIError as e:
            status_code = getattr(e, "code", None)
            is_retriable = (status_code in [429, 500, 503, 504])
            msg = str(e).lower()
            if "rate limit" in msg or "quota exceeded" in msg or "timeout" in msg or "exhausted" in msg:
                is_retriable = True

            if is_retriable and attempt < max_retries:
                time.sleep(delay)
                delay *= 2.0
            else:
                raise Exception(f"Gemini API error during {mode} analysis: {e.message if hasattr(e, 'message') else str(e)}")
        except Exception as e:
            # Do not retry validation or configuration errors
            raise Exception(f"Error generating content: {str(e)}")

    if not response:
        raise Exception(f"Gemini API returned empty response for mode {mode}")

    # 3. Parse JSON response
    try:
        response_text = response.text
        # Clean markdown code block wraps if LLM returns them despite response_mime_type
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:-1]
            response_text = "\n".join(lines)
            
        parsed_data = json.loads(response_text)
    except Exception as e:
        # Fallback in case response is empty or failed to parse
        raise Exception(f"Gemini response did not return valid JSON for mode {mode}: {str(e)}")

    # Add disclaimer if missing in the LLM response (fallback)
    if "disclaimer" not in parsed_data:
        parsed_data["disclaimer"] = getattr(schema, "model_fields", {}).get("disclaimer", {}).default or ""

    # 4. Handle Save/History Operations
    if mode == "qa":
        # Save to session history for follow-up
        session["history"].append({"role": "user", "text": question})
        session["history"].append({"role": "model", "text": parsed_data.get("answer", "")})
        # Cap to 10 turns (20 entries)
        if len(session["history"]) > 20:
            session["history"] = session["history"][-20:]
        save_session_to_disk(ticker, session)
    else:
        # Save report with metadata to data/ai_reports/{ticker}/{mode}.json
        report_meta = AIReportMeta(
            prompt_version=prompt_ver,
            model_name=AI_MODEL,
            generation_config={
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 20
            },
            timestamp=datetime.utcnow().isoformat(),
            generated_at=datetime.utcnow().isoformat(), # frontend compatibility
            documents_used=session.get("documents_used", []),
            ticker=ticker,
            mode=mode,
            report=parsed_data
        )
        
        from security_utils import safe_join, sanitize_ticker
        safe_t = sanitize_ticker(ticker)
        ticker_reports_dir = safe_join(AI_REPORTS_DIR, safe_t)
        os.makedirs(ticker_reports_dir, exist_ok=True)
        report_path = safe_join(ticker_reports_dir, f"{mode}.json")
        
        # Pydantic serialization helper supporting both v1 and v2
        if hasattr(report_meta, "model_dump"):
            serialized_data = report_meta.model_dump()
        else:
            serialized_data = report_meta.dict()

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False)

    return parsed_data


def get_saved_reports(ticker: str) -> dict:
    """Reads all saved AI reports for a ticker from disk safely."""
    from security_utils import safe_join, sanitize_ticker
    results = {}
    safe_t = sanitize_ticker(ticker)
    ticker_reports_dir = safe_join(AI_REPORTS_DIR, safe_t)
    
    if not os.path.exists(ticker_reports_dir):
        return results

    # Valid modes
    modes = ["business", "governance", "risks", "thesis"]
    for mode in modes:
        report_path = safe_join(ticker_reports_dir, f"{mode}.json")
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    results[mode] = json.load(f)
            except Exception as e:
                print(f"Error loading saved report {report_path}: {e}")
                
    return results
