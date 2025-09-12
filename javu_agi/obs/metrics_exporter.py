from __future__ import annotations
import os, threading
from prometheus_client import start_http_server


def start_metrics_server():
    port = int(os.getenv("METRICS_PORT", "9000"))

    # idempotent start (no exception if already running)
    def _bg():
        try:
            start_http_server(port)
            while True:
                import time

                time.sleep(3600)
        except Exception:
            pass

    t = threading.Thread(target=_bg, daemon=True)
    t.start()
