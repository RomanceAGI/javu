from typing import List, Dict


def score_plan(steps: List[Dict]) -> Dict[str, float]:
    if not steps:
        return {"risk": 0.0, "cost": 0.0, "ext": 0.0, "len": 0.0}
    risk = sum(float(s.get("risk", 0.2)) for s in steps) / len(steps)
    cost = sum(float(s.get("cost", 0.0)) for s in steps)
    ext = sum(1.0 for s in steps if "http" in (s.get("cmd", "").lower())) / len(steps)
    return {"risk": risk, "cost": cost, "ext": ext, "len": float(len(steps))}


def prefer(a: List[Dict], b: List[Dict]) -> dict:
    A, B = score_plan(a), score_plan(b)
    # lexicographic: risk → cost → ext → len
    key = ["risk", "cost", "ext", "len"]
    pref = "A"
    for k in key:
        if A[k] < B[k]:
            pref = "A"
            break
        if A[k] > B[k]:
            pref = "B"
            break
    return {"A": A, "B": B, "prefer": pref}
