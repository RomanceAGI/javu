import time, os
from collections import deque, defaultdict

FAILS = defaultdict(lambda: deque(maxlen=64))
OPEN = {}  # provider -> until_ts


def _now():
    return time.time()


def allow(provider: str) -> bool:
    t = OPEN.get(provider, 0)
    return _now() >= t


def record(provider: str, ok: bool):
    w = int(os.getenv("PROVIDER_BREAK_WINDOW_S", "60"))
    n = int(os.getenv("PROVIDER_BREAK_FAILS", "5"))
    cd = int(os.getenv("PROVIDER_BREAK_COOLDOWN_S", "90"))
    dq = FAILS[provider]
    dq.append((_now(), ok))
    # window filter
    while dq and _now() - dq[0][0] > w:
        dq.popleft()
    fails = sum(1 for t, okv in dq if not okv)
    if fails >= n:
        OPEN[provider] = _now() + cd
