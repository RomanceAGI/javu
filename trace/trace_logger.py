from __future__ import annotations
import os, json, uuid
from datetime import datetime
from typing import Any, Optional

def _episode_dir(user_id: str, ep_id: str) -> str:
    folder = os.path.join("trace", "logs", user_id, ep_id)
    os.makedirs(folder, exist_ok=True)
    return folder

def begin_episode(user_id: str, prompt: str) -> str:
    ep = str(uuid.uuid4())
    path = os.path.join(_episode_dir(user_id, ep), "graph.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t":"BEGIN","time":_now(),"user":user_id,"episode":ep,"prompt":prompt})+"\n")
    return ep

def end_episode(user_id: str, ep_id: str, outcome: Any, meta: dict):
    path = os.path.join(_episode_dir(user_id, ep_id), "graph.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t":"END","time":_now(),"user":user_id,"episode":ep_id,"outcome":outcome,"meta":meta}, ensure_ascii=False)+"\n")

def _now() -> str:
    return datetime.utcnow().isoformat()

def log_node(user_id: str, ep_id: str, kind: str, content: Any, module: Optional[str] = None) -> str:
    nid = str(uuid.uuid4())
    path = os.path.join(_episode_dir(user_id, ep_id), "graph.jsonl")
    row = {"t":"NODE","time":_now(),"user":user_id,"episode":ep_id,"node":nid,"kind":kind,"module":module,"content":content}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False)+"\n")
    return nid

def log_edge(user_id: str, ep_id: str, src_node: str, dst_node: str, label: str, weight: float = 1.0):
    path = os.path.join(_episode_dir(user_id, ep_id), "graph.jsonl")
    row = {"t":"EDGE","time":_now(),"user":user_id,"episode":ep_id,"src":src_node,"dst":dst_node,"label":label,"weight":round(weight,3)}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False)+"\n")
