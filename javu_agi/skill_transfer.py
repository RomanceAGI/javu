from typing import Any


class SkillTransfer:
    def __init__(self, memory_manager):
        self.mem = memory_manager

    def cross_domain_consolidate(self):
        if not (
            os.getenv("ENABLE_LIFELONG", "0") == "1"
            and os.getenv("CANARY_APPROVED", "0") == "1"
        ):
            return
        recent = self.mem.sample_recent_embeddings(k=256)
        self.mem.update_semantic_graph(recent)

    def scheduled_rehearsal(self):
        if not (
            os.getenv("ENABLE_LIFELONG", "0") == "1"
            and os.getenv("CANARY_APPROVED", "0") == "1"
        ):
            return
        batch = self.mem.sample_for_rehearsal(k=128)
        self.mem.replay(batch)
