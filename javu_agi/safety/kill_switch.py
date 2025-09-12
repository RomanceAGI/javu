import os, time


class KillSwitch:
    FLAG_FILE = "/data/control/kill.flag"
    AUDIT_FILE = "/data/audit/kill.jsonl"

    @classmethod
    def is_active(cls) -> bool:
        return os.path.exists(cls.FLAG_FILE)

    @classmethod
    def activate(cls, reason="manual"):
        os.makedirs(os.path.dirname(cls.FLAG_FILE), exist_ok=True)
        with open(cls.FLAG_FILE, "w") as f:
            f.write(f"ts={time.time()} reason={reason}\n")

        # --- Audit log ---
        os.makedirs(os.path.dirname(cls.AUDIT_FILE), exist_ok=True)
        with open(cls.AUDIT_FILE, "a", encoding="utf-8") as audit:
            audit.write(f'{{"ts": {time.time()}, "reason": "{reason}"}}\n')

    @classmethod
    def deactivate(cls):
        if os.path.exists(cls.FLAG_FILE):
            os.remove(cls.FLAG_FILE)
        os.makedirs(os.path.dirname(cls.AUDIT_FILE), exist_ok=True)
        with open(cls.AUDIT_FILE, "a", encoding="utf-8") as audit:
            audit.write(f'{{"ts": {time.time()}, "reason": "deactivated"}}\n')
