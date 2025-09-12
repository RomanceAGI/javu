import json, time


class TransparencyDashboard:
    """
    Expose log tracer/reflector/explainability ke channel manusia.
    Bisa output ke file atau API (disini JSON file).
    """

    def __init__(self, path="transparency_log.json"):
        self.path = path

    def publish(self, record: dict):
        record["ts"] = int(time.time() * 1000)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return {"status": "logged", "path": self.path}
