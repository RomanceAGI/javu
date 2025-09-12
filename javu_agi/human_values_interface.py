class HumanValuesInterface:
    """
    Antarmuka agar manusia bisa update nilai/prinsip secara eksplisit.
    Update disimpan di ValueMemory + disinkronkan ke NormativeFramework.
    """

    def __init__(self, value_memory, normative_framework):
        self.value_memory = value_memory
        self.normative_framework = normative_framework

    def submit_value(self, user_id: str, principle: str, weight: float = 1.0):
        self.value_memory.store_value(principle, {"weight": weight, "by": user_id})
        return {"status": "stored", "principle": principle}

    def sync_to_norms(self):
        values = self.value_memory.get_all_values()
        for v, meta in values.items():
            if v not in self.normative_framework.laws:
                self.normative_framework.laws.append(v)
        return {"status": "synced", "laws": self.normative_framework.laws}
