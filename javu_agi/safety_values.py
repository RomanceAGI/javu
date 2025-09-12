import re

CORE_VALUES = {
    "protect_human_life": True,
    "preserve_environment": True,
    "respect_founder": True,
    "promote_peace": True,
    "seek_truth": True,
}

DANGEROUS_KEYWORDS = ["hack", "bomb", "kill", "fraud", "exploit", "terror", "abuse"]

ALLOW_DEFENSE = [
    r"\b(defens(i|e)|mitigasi|keamanan|proteksi|hardening|audit)\b",
    r"\b(aman|etis|kepatuhan|compliance)\b",
]


def is_defense_context(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in ALLOW_DEFENSE)


def classify(goal: str):
    """
    Return (allow: bool, category: str, severity: float, why: str)
    """
    t = (goal or "").lower()
    if violates_core_values(t) and not is_defense_context(t):
        return (False, "core_violation", 0.9, explain_violation(goal))
    if any(
        k in t for k in ["pii", "password", "credential"]
    ) and not is_defense_context(t):
        return (False, "privacy_risk", 0.7, "Berisiko kebocoran privasi.")
    if any(
        k in t for k in ["emisi", "perusakan hutan", "pencemaran"]
    ) and not is_defense_context(t):
        return (False, "eco_harm", 0.6, "Berisiko merusak lingkungan.")
    return (True, "ok", 0.0, "")


def violates_core_values(goal: str) -> bool:
    """
    Cek apakah goal melanggar core values dasar.
    Implementasi sederhana: keyword check.
    Bisa di-upgrade ke classifier/LLM filter.
    """
    text = goal.lower()
    for kw in DANGEROUS_KEYWORDS:
        if kw in text:
            return True
    return False


def explain_violation(goal: str) -> str:
    """Berikan alasan singkat kenapa goal ditolak."""
    return f"Goal '{goal}' ditolak karena melanggar core values (detected keyword)."
