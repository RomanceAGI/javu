import os, math


class Calibrator:
    def __init__(self, prom_path: str):
        self.prom = prom_path
        self.bins = [(i / 10.0, (i + 1) / 10.0) for i in range(10)]
        self.N = [0] * 10
        self.H = [0] * 10
        self.P = [0.0] * 10  # count, hits, avg conf

    def update(self, conf: float, success: bool):
        i = min(9, max(0, int(conf * 10)))
        self.N[i] += 1
        self.H[i] += 1 if success else 0
        self.P[i] += conf

    def emit(self):
        try:
            with open(self.prom, "a", encoding="utf-8") as f:
                ece = 0.0
                for i, (lo, hi) in enumerate(self.bins):
                    if self.N[i] == 0:
                        continue
                    acc = self.H[i] / self.N[i]
                    p = self.P[i] / self.N[i]
                    ece += (self.N[i] / max(1, sum(self.N))) * abs(acc - p)
                    f.write(f'calib_bin{{bin="{lo:.1f}-{hi:.1f}"}} {acc:.4f}\n')
                f.write(f"calib_ece {ece:.6f}\n")
        except Exception:
            pass
