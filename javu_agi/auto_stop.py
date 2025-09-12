import os, time


class AutoStop:
    def __init__(self, gate):
        self.gate = gate

    def check_and_maybe_stop(self, errors: int, risk: float):
        e_thr = int(os.getenv("AUTOSTOP_MAX_ERRORS", "4"))
        r_thr = float(os.getenv("AUTOSTOP_MAX_RISK", "0.85"))
        if errors >= e_thr or risk > r_thr:
            try:
                self.gate.disable()
            except Exception:
                pass
            return True
        return False
