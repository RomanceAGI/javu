from __future__ import annotations
from typing import List, Dict
import os
import requests


class Plan:
    def __init__(self, steps: List[Dict]):
        self.steps = steps


class LLMPlanner:
    """
    Planner adaptif berbasis LLM.
    Mengubah perintah user jadi langkah-langkah tool yang dapat dieksekusi.
    """

    def __init__(self, llm_url: str = None, api_key: str = None):
        self.llm_url = llm_url or os.getenv("PLANNER_LLM_URL")
        self.api_key = api_key or os.getenv("PLANNER_LLM_KEY")

    def plan(self, prompt: str) -> Plan:
        if not self.llm_url or not self.api_key:
            raise RuntimeError("Planner LLM tidak dikonfigurasi.")
        payload = {
            "prompt": f"""
            Anda adalah AI planner. Ubah instruksi berikut menjadi urutan langkah tool.
            Format output: JSON list, setiap item {{ "tool": "<nama_tool>", "cmd": "<command>" }}
            Instruksi: {prompt}
            """,
            "max_tokens": 512,
        }
        resp = requests.post(
            self.llm_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        try:
            steps = resp.json().get("steps", [])
            if isinstance(steps, str):
                import json as _json

                steps = _json.loads(steps)
        except Exception:
            steps = []

        # sanitize & validate
        norm = []
        for s in steps:
            if not isinstance(s, dict):
                continue
            tool = str(s.get("tool", "")).strip() or "python"
            cmd = str(s.get("cmd", "")).strip()
            if not cmd:
                continue
            norm.append({"tool": tool, "cmd": cmd})
        steps = norm

        # fallback kalau kosong: planner ringan
        if not steps:
            from .planner import Planner as _P

            steps = _P().plan(prompt).steps
        # model-based improve (CEM-lite)
        try:
            from javu_agi.mbrl import MBPlanner
            from javu_agi.world_model import WorldModel

            wm = getattr(self, "world", None) or WorldModel()
            steps = MBPlanner(wm.mb).improve(state=prompt, base=steps)
        except Exception:
            pass
        return Plan(steps)
