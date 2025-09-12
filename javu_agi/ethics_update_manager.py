class EthicsUpdateManager:
    """
    Sinkronisasi perubahan nilai moral/etika dari budaya/konteks ke NormativeFramework.
    """

    def __init__(self, framework):
        self.framework = framework

    def update_from_context(self, context: dict):
        new_principles = context.get("principles", [])
        for p in new_principles:
            if p not in self.framework.laws:
                self.framework.laws.append(p)
        return {"status": "updated", "laws": self.framework.laws}
