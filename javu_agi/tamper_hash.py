import hashlib, json


class TamperHash:
    def __init__(self):
        self.h = hashlib.sha256()

    def feed(self, obj):
        self.h.update(json.dumps(obj, sort_keys=True).encode("utf-8"))

    def hexdigest(self):
        return self.h.hexdigest()
