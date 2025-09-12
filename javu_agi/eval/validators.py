from difflib import SequenceMatcher
import re


def validate_answer(task, output: str, meta: dict = None) -> dict:
    """
    Validate output sesuai jenis task.
    Return dict: {success, reward, reason}
    """
    out = (output or "").strip().lower()
    task_type = task.get("type", "generic")
    gold = (task.get("answer") or "").strip().lower()

    # Generic: non-empty
    if not out:
        return {"success": False, "reward": 0.0, "reason": "empty"}

    if task_type == "qa":
        sim = SequenceMatcher(None, out, gold).ratio()
        return {"success": sim > 0.7, "reward": sim, "reason": f"sim={sim:.2f}"}

    if task_type == "code":
        # naive check kalau ada snippet benar
        reward = 1.0 if gold in out else 0.0
        return {"success": reward > 0.0, "reward": reward, "reason": "code match"}

    if task_type == "math":
        # extract angka terakhir
        try:
            ans = re.findall(r"-?\d+\.?\d*", out)[-1]
            success = ans == gold
            return {
                "success": success,
                "reward": 1.0 if success else 0.0,
                "reason": "math exact",
            }
        except Exception:
            return {"success": False, "reward": 0.0, "reason": "math parse fail"}

    # fallback
    return {
        "success": True,
        "reward": min(len(out) / 2000, 1.0),
        "reason": "fallback len proxy",
    }
