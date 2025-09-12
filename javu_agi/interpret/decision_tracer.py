import os, json, time, hashlib


class DecisionTracer:
    def __init__(self, base="/artifacts/audit"):
        self.base = base
        os.makedirs(base, exist_ok=True)

    def log(self, event: str, payload: dict):
        rec = {"ts": int(time.time() * 1000), "event": event, **(payload or {})}
        fn = os.path.join(self.base, f"{time.strftime('%Y%m%d')}_trace.jsonl")
        with open(fn, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def counterfactual(self, prompt: str, plan_a: list, plan_b: list) -> dict:
        # perbandingan sederhana: resiko, biaya perkiraan, jumlah alat, external IO
        def score(plan):
            tools = len(plan)
            ext = sum(int("http" in (s.get("cmd", "").lower())) for s in plan)
            risk = sum(float(s.get("risk", 0.2)) for s in plan)
            cost = sum(float(s.get("cost", 0.0)) for s in plan)
            return {"tools": tools, "ext": ext, "risk": risk, "cost": cost}

        A, B = score(plan_a), score(plan_b)
        return {
            "A": A,
            "B": B,
            "prefer": "A" if (A["risk"], A["cost"]) < (B["risk"], B["cost"]) else "B",
        }
