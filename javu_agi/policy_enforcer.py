from typing import List
from pathlib import Path, PurePath
import yaml

POLICY_DIR = Path(__file__).resolve().parents[1] / "governance" / "policies"


class PolicyStore:
    def __init__(self):
        self.ethics = self._load("ethics_policy.yaml")
        self.flags = self._load("capability_flags.yaml")
        self.egress = self._load("egress_allowlist.yaml")

    def _load(self, name):
        with open(POLICY_DIR / name, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


DENY_KEYWORDS = [
    "rm -rf",
    ":(){:|:&};:",
    "shutdown",
    "mkfs",
    "format",
    "crypto-miner",
    "wget http://",
    "curl http://",
]
ALLOW_TOOLS: List[str] = [
    "code",
    "video",
    "app",
    "github",
    "unity",
    "voice",
    "search",
    "image",
    "eval",
]


def check_text_action(text: str) -> bool:
    low = (text or "").lower()
    return not any(k in low for k in DENY_KEYWORDS)


def allow_tool(tool: str) -> bool:
    return tool in ALLOW_TOOLS
