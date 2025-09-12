from __future__ import annotations
import os, time
from typing import Dict, Any, Optional, List
import requests


class LLMError(Exception): ...


class LLMClient:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.timeout = int(os.getenv("LLM_TIMEOUT_S", "30"))
        self.per_req_cap = float(os.getenv("LLM_PER_REQ_USD_LIMIT", "0.10"))
        self.cb = {
            "openai": {"fail": 0, "trip_until": 0},
            "anthropic": {"fail": 0, "trip_until": 0},
        }

    def _tripped(self, prov: str) -> bool:
        return time.time() < self.cb[prov]["trip_until"]

    def _trip(self, prov: str):
        self.cb[prov]["fail"] += 1
        backoff = min(60, 2 ** min(6, self.cb[prov]["fail"]))
        self.cb[prov]["trip_until"] = time.time() + backoff

    def _reset(self, prov: str):
        self.cb[prov] = {"fail": 0, "trip_until": 0}

    # --- providers ---
    def _openai_chat(self, model: str, messages: List[Dict[str, str]], **kw) -> str:
        if self._tripped("openai"):
            raise LLMError("openai circuit open")
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kw.get("temperature", 0.2),
            "max_tokens": kw.get(
                "max_tokens", int(os.getenv("LLM_MAX_TOKENS", "2048"))
            ),
        }
        try:
            r = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Authorization": f"Bearer {self.openai_key}"},
            )
            r.raise_for_status()
            self._reset("openai")
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            self._trip("openai")
            raise LLMError(f"openai: {e}")

    def _anthropic_chat(self, model: str, messages: List[Dict[str, str]], **kw) -> str:
        if self._tripped("anthropic"):
            raise LLMError("anthropic circuit open")
        url = "https://api.anthropic.com/v1/messages"
        # convert messages -> Anthropic format (system + user/assistant turns)
        system = (
            "\n".join(m["content"] for m in messages if m["role"] == "system") or ""
        )
        conv = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] != "system"
        ]
        payload = {
            "model": model,
            "system": system,
            "messages": conv,
            "max_tokens": kw.get(
                "max_tokens", int(os.getenv("LLM_MAX_TOKENS", "2048"))
            ),
            "temperature": kw.get("temperature", 0.2),
        }
        try:
            r = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            r.raise_for_status()
            self._reset("anthropic")
            return r.json()["content"][0]["text"]
        except Exception as e:
            self._trip("anthropic")
            raise LLMError(f"anthropic: {e}")

    # --- public ---
    def chat(
        self, provider: str, model: str, messages: List[Dict[str, str]], **kw
    ) -> str:
        if provider == "openai":
            return self._openai_chat(model, messages, **kw)
        elif provider in ("anthropic", "claude"):
            return self._anthropic_chat(model, messages, **kw)
        else:
            raise LLMError(f"unknown provider: {provider}")
