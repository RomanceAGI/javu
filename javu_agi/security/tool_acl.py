import os, json
from functools import lru_cache


@lru_cache(maxsize=1)
def _load_acl():
    p = os.getenv("TOOL_ACL_PATH", "/opt/agi/governance/tool_acl.json")
    try:
        return json.load(open(p, "r", encoding="utf-8"))
    except Exception:
        return {"default_allow": ["search", "code"], "users": {}}


def is_tool_allowed(user_id: str, tool: str) -> bool:
    tool = (tool or "").lower()
    A = _load_acl()
    allow = set(map(str.lower, A.get("default_allow", [])))
    deny = set(map(str.lower, A.get("default_deny", [])))
    U = A.get("users", {}).get(user_id) or {}
    allow |= set(map(str.lower, U.get("allow", [])))
    deny |= set(map(str.lower, U.get("deny", [])))
    if tool in deny:
        return False
    if allow and tool not in allow:
        return False
    return True
