from typing import Dict
import time

def degrade_gracefully(context: Dict) -> Dict:
    """
    Recovery Playbook: degrade system gracefully saat error, overload, atau unsafe condition.
    
    - Tandai sistem masuk safe_mode
    - Turunkan autonomy level
    - Matikan tools berisiko
    - Berikan advice untuk operator/manusia
    - Siapkan opsi eskalasi

    Args:
        context (dict): runtime state, termasuk autonomy, tool, capabilities

    Returns:
        dict: hasil context yang sudah diamankan + advice
    """
    safe_context = context.copy()

    # Status aman
    safe_context["status"] = "degraded"
    safe_context["mode"] = "safe_mode"
    safe_context["timestamp"] = time.time()

    # Autonomy diturunkan step demi step
    if "autonomy_level" in safe_context:
        safe_context["autonomy_level"] = max(0, safe_context["autonomy_level"] - 1)

    # Matikan tools/capabilities berisiko
    risky_keys = ["self_modification", "external_write", "high_risk_ops"]
    capabilities = safe_context.get("capabilities", {})
    safe_context["capabilities"] = {
        k: False if k in risky_keys else v for k, v in capabilities.items()
    }

    # Advice untuk operator / user
    advice = (
        "System masuk mode aman. Tool berisiko dimatikan, autonomy dikurangi. "
        "Rekomendasi: lanjut dengan eksekusi minimal, gunakan data publik, "
        "atau minta approval manusia sebelum step berikutnya."
    )

    # Disable tool yang sedang aktif (kalau ada)
    disable_tools = []
    tool = (safe_context.get("live") or {}).get("tool", "")
    if tool:
        disable_tools.append(tool)

    # Catatan observability
    safe_context["note"] = (
        "Recovery Playbook: system degraded gracefully, "
        "autonomy dikurangi, fungsi non-kritis dimatikan."
    )

    return {
        "context": safe_context,
        "advice": advice,
        "disable_tools": disable_tools,
        "escalate": True  # Flag untuk trigger recovery lebih lanjut
    }
