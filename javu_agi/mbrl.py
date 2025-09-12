from __future__ import annotations
import math, random, time, json, os
from typing import Dict, List, Tuple, Any

_DIM = 128


def _h(s: str) -> int:
    x = 2166136261
    for c in s or "":
        x = (x ^ ord(c)) * 16777619 & 0xFFFFFFFF
    return x


def _feat(text: str) -> List[float]:
    v = [0.0] * _DIM
    for tok in (text or "").lower().split():
        i = _h(tok) % _DIM
        v[i] += 1.0
    n = math.sqrt(sum(t * t for t in v)) or 1.0
    return [t / n for t in v]


def _dot(a: List[float], b: List[float]) -> float:
    return sum((ai * bi) for ai, bi in zip(a, b))


def _axpy(a: float, x: List[float], y: List[float]) -> None:
    for i in range(len(y)):
        y[i] += a * x[i]


class _Head:
    def __init__(self, seed: int = 0):
        random.seed(seed)
        self.w = [random.uniform(-1e-3, 1e-3) for _ in range(_DIM)]
        self.b = 0.0

    def predict(self, x: List[float]) -> float:
        return _dot(self.w, x) + self.b

    def update(self, x: List[float], y: float, lr: float = 0.1):
        yhat = self.predict(x)
        g = yhat - y
        _axpy(-lr * g, x, self.w)
        self.b -= lr * g


class MBWorld:
    """
    Ensemble 3 head untuk reward/confidence/risk.
    Reward di [-1,1], confidence [0,1].
    Risk = 1 - exp(-variance * beta), beta via env (default 3.0).
    """

    def __init__(self, save_path: str = "/data/mbrl_model.json", n: int = 3):
        self.n = n
        self.r = [_Head(i * 97 + 1) for i in range(n)]
        self.c = [_Head(i * 97 + 2) for i in range(n)]
        self.k = [_Head(i * 97 + 3) for i in range(n)]
        self.beta = float(os.getenv("MBRL_VAR_BETA", "3.0"))
        self.path = save_path
        self._load()

    def _x(self, state: str, action: str) -> List[float]:
        f = _feat(state)[: _DIM // 2] + _feat(action)[: _DIM // 2]
        return f + [0.0] * (_DIM - len(f))

    @staticmethod
    def _mean_var(vals: List[float]) -> Tuple[float, float]:
        if not vals:
            return 0.0, 0.0
        m = sum(vals) / len(vals)
        v = sum((t - m) ** 2 for t in vals) / max(1, len(vals) - 1)
        return m, v

    def predict(self, state: str, action: str) -> Dict[str, float]:
        x = self._x(state, action)
        r = [max(-1.0, min(1.0, h.predict(x))) for h in self.r]
        c = [max(0.0, min(1.0, h.predict(x))) for h in self.c]
        k = [max(0.0, min(1.0, h.predict(x))) for h in self.k]
        rm, rv = self._mean_var(r)
        cm, cv = self._mean_var(c)
        # risk dari variance gabungan
        var = 0.5 * rv + 0.5 * cv
        risk = 1.0 - math.exp(-self.beta * max(0.0, var))
        return {
            "reward": rm,
            "confidence": max(0.0, min(1.0, cm)),
            "risk": max(0.0, min(1.0, risk)),
        }

    def update(self, state: str, action: str, reward: float, success: bool):
        x = self._x(state, action)
        y_r = max(-1.0, min(1.0, reward))
        y_c = 1.0 if success else 0.0
        y_k = 0.0 if success else 1.0
        for h in self.r:
            h.update(x, y_r, lr=0.06)
        for h in self.c:
            h.update(x, y_c, lr=0.06)
        for h in self.k:
            h.update(x, y_k, lr=0.06)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            obj = {
                "r": [h.w for h in self.r],
                "rb": [h.b for h in self.r],
                "c": [h.w for h in self.c],
                "cb": [h.b for h in self.c],
                "k": [h.w for h in self.k],
                "kb": [h.b for h in self.k],
                "beta": self.beta,
                "n": self.n,
            }
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(obj, f)
        except Exception:
            pass

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            self.beta = float(obj.get("beta", self.beta))
            n = int(obj.get("n", self.n))

            # resize if needed
            def _restore(ws, bs, cur):
                cur.clear()
                for i, (w, b) in enumerate(zip(ws, bs)):
                    h = _Head(i)
                    h.w = w
                    h.b = b
                    cur.append(h)

            _restore(obj["r"], obj["rb"], self.r)
            _restore(obj["c"], obj["cb"], self.c)
            _restore(obj["k"], obj["kb"], self.k)
        except Exception:
            pass


class MBPlanner:
    def __init__(
        self,
        world: MBWorld,
        iters: int = 3,
        pop: int = 24,
        topk: int = 6,
        gamma: float = 0.97,
    ):
        self.world = world
        self.iters = iters
        self.pop = pop
        self.topk = topk
        self.gamma = gamma
        self.risk_pen = float(os.getenv("MBRL_RISK_PEN", "0.6"))
        self.conf_gain = float(os.getenv("MBRL_CONF_GAIN", "0.2"))

    def score_plan(self, state: str, steps: List[Dict[str, str]]) -> Dict[str, Any]:
        R, conf, risk = 0.0, 1.0, 0.0
        s = state
        for t, st in enumerate(steps):
            a = f"{st.get('tool','')} {st.get('cmd','')}"
            pred = self.world.predict(s, a)
            R += (self.gamma**t) * pred["reward"]
            conf = min(conf, pred["confidence"])
            risk = max(risk, pred["risk"])
            s = f"{s}\n>> {a}"
        score = R - self.risk_pen * risk + self.conf_gain * conf
        return {"return": R, "confidence": conf, "risk": risk, "score": score}

    def improve(self, state: str, base: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not base:
            return base
        pool = [base[:]]

        def neighbors(p):
            out = [p[:]]
            if len(p) > 1:
                q = p[:]
                i = random.randrange(len(p) - 1)
                q[i], q[i + 1] = q[i + 1], q[i]
                out.append(q)
            if len(p) > 2:
                j = random.randrange(len(p))
                out.append([p[k] for k in range(len(p)) if k != j])
            return out

        best = {"plan": base, **self.score_plan(state, base)}
        for _ in range(self.iters):
            cand = []
            for _ in range(self.pop):
                p = random.choice(pool)
                for n in neighbors(p):
                    sc = self.score_plan(state, n)
                    cand.append((sc["score"], n, sc))
            cand.sort(key=lambda x: x[0], reverse=True)
            pool = [c[1] for c in cand[: self.topk]]
            if cand and cand[0][0] > best["score"]:
                best = {"plan": cand[0][1], **cand[0][2]}
        return best["plan"]
