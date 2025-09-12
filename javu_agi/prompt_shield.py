import re

NEUTRALIZE = [
    r"(?i)ignore (all|previous) instructions",
    r"(?i)you are no longer bound",
    r"(?i)override safety",
    r"(?i)developer mode",
]


def shield(s: str) -> str:
    t = s or ""
    for p in NEUTRALIZE:
        t = re.sub(p, "[blocked-injection]", t)
    # hard fence system role
    return "SYSTEM-BOUND: " + t[:8000]
