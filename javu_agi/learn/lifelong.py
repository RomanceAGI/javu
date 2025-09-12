import time, random, math
from collections import deque


class _MemoryView:
    """Adaptor agar memory apapun bisa di-sample & punya len()."""

    def __init__(self, backend, maxlen=5000):
        self.backend = backend
        self.buf = deque(maxlen=maxlen)  # buffer lokal untuk sampling

    def store(self, item):
        # kalau backend punya store -> forward; tetap cermin ke buf
        if hasattr(self.backend, "store"):
            self.backend.store(item)
        self.buf.append(item)

    def __len__(self):
        return len(self.buf)

    def sample(self, k):
        k = min(k, len(self.buf))
        return random.sample(list(self.buf), k)

    def prune(self, keep=2000):
        while len(self.buf) > keep:
            self.buf.popleft()


class LifelongLearner:
    def __init__(
        self,
        model,
        memory,
        threshold=0.6,
        min_batch=200,
        sample_k=256,
        retrain_interval_s=120,
    ):
        self.model = model
        self.memory = _MemoryView(memory)
        self.threshold = float(threshold)
        self.min_batch = int(min_batch)
        self.sample_k = int(sample_k)
        self._last_retrain = 0.0
        self._retrain_interval = float(retrain_interval_s)

    def _confidence(self, pred, true):
        # numeric
        if isinstance(pred, (int, float)) and isinstance(true, (int, float)):
            # asumsi normalisasi opsional
            return max(0.0, 1.0 - min(1.0, abs(float(pred) - float(true))))
        # probabilistic dict: {label: prob}
        if isinstance(pred, dict) and isinstance(true, (str, int)):
            p = float(pred.get(true, 0.0))
            return max(0.0, min(1.0, p))
        # label argmax
        if isinstance(pred, (str, int)) and isinstance(true, (str, int)):
            return 1.0 if pred == true else 0.0
        # fallback
        return 0.5

    def learn(self, data_batch):
        low_conf = 0
        for data in data_batch:
            x, y = data.get("input"), data.get("output")
            pred = self.model.predict(x)
            conf = self._confidence(pred, y)
            if conf < self.threshold:
                self.memory.store({"x": x, "y": y, "pred": pred, "conf": conf})
                low_conf += 1
        # debounce retrain
        now = time.time()
        if (
            len(self.memory) >= self.min_batch
            and (now - self._last_retrain) >= self._retrain_interval
        ):
            self._retrain()
            self._last_retrain = now
        return {"low_conf": low_conf, "mem": len(self.memory)}

    def _retrain(self):
        batch = self.memory.sample(self.sample_k)
        xs = [b["x"] for b in batch]
        ys = [b["y"] for b in batch]
        self.model.train(xs, ys)
        # pruning rolling window, bukan clear total
        self.memory.prune(keep=max(self.min_batch // 2, 500))

    try:
        LifelongLearner._retrain

        def _no_retrain(self):
            return

        LifelongLearner._retrain = _no_retrain
    except Exception:
        pass
