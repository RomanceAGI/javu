from javu_agi.memory.memory import recall_from_memory, save_to_memory
import os, time, json, hashlib
from typing import List, Dict, Any, Optional

CANARY = (
    os.getenv("ENABLE_LIFELONG", "0") == "1"
    and os.getenv("CANARY_APPROVED", "0") == "1"
)
EPISODE_TAG = "[EPISODE]"
REFLECT_TAG = "[REFLECTION]"
KNOWLEDGE_TAG = "[KNOWLEDGE]"
POLICY_TAG = "[POLICY UPDATE]"
REHEARSE_TAG = "[REHEARSAL]"


def _audit(kind: str, rec: Dict[str, Any]):
    try:
        from javu_agi.audit.audit_chain import AuditChain

        AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain")).commit(
            kind=kind, record=rec
        )
    except Exception:
        pass


class ContinualLearner:
    """
    Continual behavioral learning (tanpa fine-tune foundation).
    Stage: ingest -> reflect -> consolidate -> policy_update -> rehearsal.
    Gated by ENV: ENABLE_LIFELONG=1 & CANARY_APPROVED=1.
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.enabled = CANARY
        self.buf: List[Dict[str, Any]] = []
        # guard: DP budget / minimal logging only
        self.dp_eps = float(os.getenv("CL_DP_EPS", "0.0"))
        self.max_buf = int(os.getenv("CL_BUF_MAX", "32"))
        self.min_batch = int(os.getenv("CL_MIN_BATCH", "4"))

    # --- ingest ---
    def ingest(self, event: Dict[str, Any]):
        if not self.enabled:
            return
        evt = {
            k: v
            for k, v in (event or {}).items()
            if k in ("goal", "steps", "result", "reward", "cost")
        }
        evt["ts"] = int(time.time())
        self.buf.append(evt)
        self.buf = self.buf[-self.max_buf :]
        save_to_memory(
            self.user_id, f"{EPISODE_TAG} {json.dumps(evt, ensure_ascii=False)}"
        )

    # --- reflection ---
    def reflect(self) -> Dict[str, Any]:
        if not self.enabled or len(self.buf) < self.min_batch:
            return {"ok": False, "reason": "insufficient_batch"}
        # simple patterning: kegagalan berulang & langkah tidak efektif
        fails = [
            b
            for b in self.buf
            if str(b.get("result", "")).startswith("fail") or b.get("reward", 0.0) < 0.3
        ]
        repeated = {}
        for b in self.buf:
            for s in b.get("steps") or []:
                k = (s.get("tool"), s.get("cmd", "")[:24])
                repeated[k] = repeated.get(k, 0) + 1
        hotspots = sorted(repeated.items(), key=lambda x: x[1], reverse=True)[:3]
        ref = {"n": len(self.buf), "fails": len(fails), "hotspots": hotspots}
        save_to_memory(
            self.user_id, f"{REFLECT_TAG} {json.dumps(ref, ensure_ascii=False)}"
        )
        _audit("continual_reflect", ref)
        return {"ok": True, **ref}

    # --- consolidation ---
    def consolidate(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "reason": "disabled"}
        eps = (
            recall_from_memory(self.user_id, query="", top_k=50, tag=REFLECT_TAG) or ""
        ).splitlines()
        summary = f"Abstraksi dari {len(eps)} pengalaman"
        save_to_memory(self.user_id, f"{KNOWLEDGE_TAG} {summary}")
        _audit("continual_consolidate", {"episodes": len(eps)})
        return {"ok": True, "summary": summary}

    # --- policy update (behavioral, non-parametric) ---
    def update_policy(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "reason": "disabled"}
        refs = (
            recall_from_memory(self.user_id, query="", top_k=50, tag=REFLECT_TAG) or ""
        ).splitlines()
        patterns = [r for r in refs if ("berulang" in r) or ("tidak efektif" in r)]
        if not patterns:
            return {"ok": True, "updated": False}
        upd = f"Perubahan strategi berdasarkan {len(patterns)} refleksi."
        save_to_memory(self.user_id, f"{POLICY_TAG} {upd}")
        _audit("continual_policy_update", {"count": len(patterns)})
        return {"ok": True, "updated": True, "msg": upd}

    # --- spaced rehearsal (prompt recipes / SkillGraph reuse) ---
    def rehearse(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "reason": "disabled"}
        try:
            from javu_agi.learn.skill_graph import SkillGraph

            sg = SkillGraph(cache_dir=os.getenv("SKILL_CACHE_DIR", "/data/skill_cache"))
            reused = sg.reuse_ratio() if hasattr(sg, "reuse_ratio") else 0.0
        except Exception:
            reused = 0.0
        plan = {"interval_s": 600, "reuse_ratio": reused}
        save_to_memory(self.user_id, f"{REHEARSE_TAG} {json.dumps(plan)}")
        _audit("continual_rehearse", plan)
        return {"ok": True, **plan}


# ---- Backward-compatible shims (API lama tetap jalan) ----
_SINGLETON = ContinualLearner(user_id=os.getenv("CL_USER", "default"))


def ingest_experience(user_id: str, event: str):
    _SINGLETON.ingest({"goal": "freeform", "steps": [], "result": event})


def consolidate_knowledge(user_id: str):
    _SINGLETON.consolidate()


def update_policy_from_reflection(user_id: str):
    _SINGLETON.update_policy()
