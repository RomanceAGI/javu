import time
from javu_agi.ops.retention import sweep

if __name__ == "__main__":
    while True:
        try:
            sweep()
        except Exception:
            pass
        time.sleep(3600)
