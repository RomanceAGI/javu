from __future__ import annotations
import os, json, tempfile, threading, time
from typing import Dict, Any
from javu_agi.audit.audit_chain import AuditChain

IDENTITY_DIR = os.getenv("IDENTITY_DIR", "db/identities")
os.makedirs(IDENTITY_DIR, exist_ok=True)
_AUDIT = AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain"))
_LOCKS: Dict[str, threading.Lock] = {}

_SCHEMA = {
    "name": str,
    "role": str,
    "traits": list,  # list[str]
    # optional fields tolerated:
    # "profile", "prefs", "policy_overrides"
}


def identity_path(user_id: str) -> str:
    return os.path.join(IDENTITY_DIR, f"{user_id}.json")


def _default() -> Dict[str, Any]:
    return {"name": "JAVU", "role": "Digital AGI", "traits": []}


def _validate(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return _default()
    out = _default()
    out.update(
        {
            k: v
            for k, v in data.items()
            if k in {"name", "role", "traits", "profile", "prefs", "policy_overrides"}
        }
    )
    if not isinstance(out["name"], str):
        out["name"] = "JAVU"
    if not isinstance(out["role"], str):
        out["role"] = "Digital AGI"
    if not isinstance(out.get("traits", []), list):
        out["traits"] = []
    return out


def _lock_for(uid: str) -> threading.Lock:
    if uid not in _LOCKS:
        _LOCKS[uid] = threading.Lock()
    return _LOCKS[uid]


def load_identity(user_id: str) -> Dict[str, Any]:
    path = identity_path(user_id)
    with _lock_for(user_id):
        if os.path.exists(path):
            try:
                data = json.load(open(path, "r", encoding="utf-8"))
                val = _validate(data)
                _AUDIT.commit("identity:load", {"user": user_id, "ok": True})
                return val
            except Exception:
                _AUDIT.commit("identity:load", {"user": user_id, "ok": False})
                return _default()
        else:
            _AUDIT.commit("identity:load", {"user": user_id, "ok": True, "new": True})
            return _default()


def save_identity(user_id: str, data: Dict[str, Any]) -> None:
    path = identity_path(user_id)
    val = _validate(data)
    with _lock_for(user_id):
        # atomic write
        d = os.path.dirname(path)
        os.makedirs(d, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=d, encoding="utf-8"
        ) as tf:
            json.dump(val, tf, indent=2, ensure_ascii=False)
            tmp = tf.name
        os.replace(tmp, path)
        _AUDIT.commit("identity:save", {"user": user_id, "size": len(json.dumps(val))})
