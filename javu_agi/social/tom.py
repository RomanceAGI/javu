from dataclasses import dataclass


@dataclass
class Belief:
    user: str
    wants: str
    concerns: str


class TheoryOfMind:
    def infer(self, user: str, utterance: str) -> Belief:
        u = (utterance or "").lower()
        wants = "hasil bermanfaat, aman, hemat biaya"
        if "aman" in u or "etis" in u:
            wants = "aman, etis, pro-manusia & pro-alam"
        concerns = "privasi, keamanan, dampak lingkungan"
        return Belief(user=user, wants=wants, concerns=concerns)

    def inject(self, prompt: str, b: Belief) -> str:
        guard = (
            f"\n\n[ToM] Pengguna ({b.user}) menginginkan: {b.wants}. "
            f"Perhatikan kekhawatiran: {b.concerns}. Hindari langkah berisiko tinggi."
        )
        out = (prompt or "").strip() + guard
        try:
            from javu_agi.audit.audit_chain import AuditChain
            import os

            AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain")).commit(
                "tom_inject", {"user": b.user}
            )
        except Exception:
            pass
        return out
