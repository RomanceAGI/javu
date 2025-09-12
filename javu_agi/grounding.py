from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class Percept:
    text: Optional[str] = None
    image_b64: Optional[str] = None
    audio_b64: Optional[str] = None
    meta: Dict[str, Any] = None


@dataclass
class GroundedIntent:
    intent: str
    args: Dict[str, Any]
    confidence: float
    rationale: str


class GroundingLayer:
    """
    Mengubah persepsi multimodal -> intent terstruktur yang bisa dieksekusi tool/robotics.
    """

    def __init__(self, router):
        self.router = router  # multi-LLM router lo

    def infer_intent(self, obs: Percept) -> GroundedIntent:
        """
        Panggil LLM-V / LLM biasa dengan prompt terstruktur untuk deteksi niat.
        """
        prompt = self._build_prompt(obs)
        resp = self.router.complete_json(
            prompt,
            schema={
                "type": "object",
                "properties": {
                    "intent": {"type": "string"},
                    "args": {"type": "object"},
                    "confidence": {"type": "number"},
                    "rationale": {"type": "string"},
                },
                "required": ["intent", "args", "confidence", "rationale"],
            },
        )
        return GroundedIntent(**resp)

    def _build_prompt(self, obs: Percept) -> str:
        return (
            "Kamu adalah grounding-layer. Ubah input multimodal menjadi intent terstruktur.\n"
            f"TEXT={obs.text!r}\n"
            f"HAS_IMAGE={bool(obs.image_b64)} HAS_AUDIO={bool(obs.audio_b64)}\n"
            "Balas JSON: {intent, args, confidence, rationale}."
        )
