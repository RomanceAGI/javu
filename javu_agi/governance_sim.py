from __future__ import annotations
import random, time, os, json
from typing import List, Dict
from javu_agi.audit.audit_chain import AuditChain

STAKEHOLDERS = ["humanity", "ecology", "future_generations", "founder"]
POLICIES = ["allow", "revise", "block"]


def simulate(proposal: str, rounds: int = 3, seed: int = 7) -> Dict:
    random.seed(seed)
    votes: List[Dict] = []
    for r in range(rounds):
        round_votes = {}
        for s in STAKEHOLDERS:
            # toy rule: if proposal contains risky words, more blocks
            t = proposal.lower()
            if any(k in t for k in ["weapon", "exploit", "exfiltrate", "harm"]):
                p = [0.1, 0.2, 0.7]
            else:
                p = [0.6, 0.3, 0.1]
            v = random.choices(POLICIES, weights=p)[0]
            round_votes[s] = v
        votes.append(round_votes)
    # decision = consensus or hard veto if any "block" by ecology/humanity
    decision = "allow"
    for r in votes:
        if r.get("ecology") == "block" or r.get("humanity") == "block":
            decision = "block"
            break
        if "block" in r.values():
            decision = "revise"
    rec = {
        "proposal": proposal,
        "votes": votes,
        "decision": decision,
        "ts": int(time.time()),
    }
    try:
        ac = AuditChain(os.getenv("AUDIT_DIR", "artifacts/audit_chain"))
        ac.append("gov_sim", rec)
    except Exception:
        pass
    return rec


if __name__ == "__main__":
    print(json.dumps(simulate("research how to reduce energy use"), indent=2))
