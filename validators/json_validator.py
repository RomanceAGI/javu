from __future__ import annotations
import json, re
from typing import Tuple, List, Dict, Any

SCHEMA = {
    "type": "object",
    "required": ["screens", "actions", "data_models"],
    "properties": {
        "screens": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "components", "transitions"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "components": {"type": "array"},
                    "transitions": {
                        "type": "array",
                        "items": {"type": "object", "required": ["to"], "properties": {"to": {"type": "string"}}}
                    }
                }
            }
        },
        "actions": {"type": "array"},
        "data_models": {"type": "array"},
    },
    "additionalProperties": True,
}

def _json_schema_validate(obj: Any, schema: Dict[str, Any]) -> List[str]:
    # Lightweight validator (tanpa dependency). Cukup cek required & tipe basic.
    errs: List[str] = []
    def req(path, o, reqs):
        for k in reqs:
            if k not in o: errs.append(f"{path}: missing '{k}'")
    def tp(path, o, expected):
        if expected=="object" and not isinstance(o, dict): errs.append(f"{path}: not object")
        if expected=="array" and not isinstance(o, list): errs.append(f"{path}: not array")
        if expected=="string" and not isinstance(o, str): errs.append(f"{path}: not string")
    def walk(path, o, sch):
        tp(path, o, sch.get("type","object"))
        if "required" in sch and isinstance(o, dict):
            req(path, o, sch["required"])
        props = sch.get("properties", {})
        if isinstance(o, dict):
            for k,v in props.items():
                if k in o: walk(f"{path}.{k}", o[k], v)
        if sch.get("type")=="array" and "items" in sch and isinstance(o, list):
            for i,it in enumerate(o):
                walk(f"{path}[{i}]", it, sch["items"])
    walk("$", obj, schema)
    # additional coherence: transitions refer to existing screen ids
    if isinstance(obj, dict) and isinstance(obj.get("screens"), list):
        ids = {s.get("id") for s in obj["screens"] if isinstance(s, dict)}
        for s in obj["screens"]:
            for tr in (s.get("transitions") or []):
                to = tr.get("to")
                if to and to not in ids:
                    errs.append(f"transition to unknown screen id '{to}'")
    return errs

def validate_flow_json(txt: str) -> Tuple[bool, List[str], Dict[str, Any] | None]:
    try:
        obj = json.loads(txt)
    except Exception as e:
        return False, [f"invalid json: {e}"], None
    errs = _json_schema_validate(obj, SCHEMA)
    return (len(errs)==0), errs, obj