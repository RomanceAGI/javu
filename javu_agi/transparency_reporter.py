from __future__ import annotations
import json, os, time, hashlib
from typing import Any, Dict


def _safe(o: Any) -> Any:
    try:
        json.dumps(o)
        return o
    except Exception:
        return str(o)


def make_report(
    request: Dict[str, Any],
    response: Dict[str, Any] | None,
    guards: Dict[str, Any],
    duration_s: float,
) -> Dict[str, Any]:
    rid = hashlib.sha1(
        f"{time.time()}:{request.get('user_id','')}".encode()
    ).hexdigest()[:12]
    md = {
        "id": rid,
        "ts": int(time.time()),
        "user_id": request.get("user_id"),
        "prompt": request.get("prompt"),
        "duration_s": round(duration_s, 4),
        "guards": guards,
        "status": (response or {}).get("status"),
        "error": (response or {}).get("error"),
        "model": (response or {}).get("model"),
        "policies": {
            "policy_vendor_block": os.getenv("POLICY_VENDOR_BLOCK", "1"),
            "training_enabled": os.getenv("TRAINING_ENABLED", "0"),
        },
    }
    md["markdown"] = (
        f"# decision {md['id']}\n"
        f"- user: {md['user_id']}\n"
        f"- duration_s: {md['duration_s']}\n"
        f"- status: {md['status']}\n"
        f"- model: {md['model']}\n"
        f"- eco_risk: {guards.get('eco',{}).get('risk')}\n"
        f"- error: {md['error']}\n\n"
        f"## prompt\n\n{md['prompt']}\n"
    )
    rec = json.loads(json.dumps(md, default=_safe))
    try:
        fn = os.getenv("TRANSPARENCY_LOG", "artifacts/transparency.jsonl")
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        base = os.getenv("TRANSPARENCY_WORM_DIR", "artifacts/worm")
        os.makedirs(base, exist_ok=True)
        open(os.path.join(base, f"{rec['id']}.json"), "w", encoding="utf-8").write(
            json.dumps(rec, ensure_ascii=False, indent=2)
        )
        open(os.path.join(base, f"{rec['id']}.md"), "w", encoding="utf-8").write(
            rec["markdown"]
        )
        # integrity hash (chain local)
        h = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
        chain = os.path.join(base, "worm_hash_chain.txt")
        with open(chain, "a", encoding="utf-8") as f:
            f.write(h + "\n")
    except Exception:
        pass
    return rec


# helper untuk bundling ke evidence pack
def export_transparency_bundle(out_dir: str = None) -> str:
    out_dir = out_dir or os.getenv("ARTIFACTS_DIR", "artifacts")
    try:
        import shutil

        worm = os.getenv("TRANSPARENCY_WORM_DIR", "artifacts/worm")
        dst = os.path.join(out_dir, "transparency_bundle")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(worm, dst, dirs_exist_ok=True)
        return dst
    except Exception:
        pass
