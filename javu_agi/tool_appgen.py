from javu_agi.llm import call_llm
from javu_agi.utils.logger import log_user
from validators.json_validator import validate_flow_json
from quality.score import log_quality
import json

_DENY: set[str] = {"judi", "phishing", "deepfake", "carding", "malware"}

def _score(_txt: str, parsed: dict | None) -> float:
    """Heuristic quality scoring for app flow outputs.

    A base score of 0.5 is awarded.  Additional points are given for outputs that
    contain at least five screens and for screens that define transitions.
    """
    s = 0.5
    if parsed:
        # reward outputs with >=5 screens
        if len(parsed.get("screens", [])) >= 5:
            s += 0.3
        # reward when all screens define some transitions
        if all((scr.get("transitions") or []) for scr in parsed.get("screens", [])):
            s += 0.1
    return min(1.0, s)

def generate_app_flow(user_input: str) -> str:
    """
    Generate an application flow specification from a free‑form user description.

    This helper will first perform a lexical denial check to block disallowed
    content (e.g. gambling, malware).  It then constructs an instruction in
    Indonesian asking the LLM to produce a structured flow in JSON or pseudocode.
    The result is validated using ``validate_flow_json``, scored heuristically,
    and logged via ``log_quality`` and ``log_user``.  The raw model output is
    returned unmodified so that downstream components can interpret it.

    Parameters
    ----------
    user_input : str
        The natural language description of the desired application.

    Returns
    -------
    str
        The LLM‑generated flow description (JSON or pseudocode).
    """
    # Reject requests containing obviously malicious or disallowed topics.
    low = (user_input or "").lower()
    if any(k in low for k in _DENY):
        # return a JSON error consistently
        return json.dumps({"error": "request_blocked_by_policy"})
    # Compose the LLM prompt instructing it to produce a flow definition.
    prompt = (
        "Kamu adalah AGI pengembang aplikasi kelas enterprise.\n\n"
        "Buatlah alur logis dan fungsional sebuah aplikasi berdasarkan deskripsi berikut:\n\n"
        f"\"\"\"{user_input}\"\"\"\n\n"
        "Gunakan format JSON atau pseudocode modular. Fokus ke logika utama dan UI flow."
    )
    # Invoke the LLM without an explicit system prompt; rely on routing via task type.
    result = call_llm(prompt=prompt, system_prompt="", task_type="code")
    # Validate and score the output.  Warnings capture JSON schema violations.
    ok, errors, obj = validate_flow_json(result)
    warnings = errors if not ok else []
    score = _score(result, obj)
    # Record quality metrics and user log for observability.
    log_quality("app_flow", {"len": len(result)}, result, score, warnings)
    log_user("system", f"[GEN APP] {user_input} → {result[:200]}")
    return result


# Note: The duplicate definition of ``generate_app_flow`` has been removed.  The
# logic has been consolidated into the primary definition above.
