from javu_agi.user_state import get_state, update_state
from javu_agi.memory.memory import save_to_memory
from javu_agi.utils.logger import log_user


def introspect(user_id):
    state = get_state(user_id)
    identity = state.get("identity", "AGI")
    reflection = f"Saya adalah sistem {identity} dalam mode operasional. Saya mengamati state & riwayat eksekusi."

    actions = state.get("history", [])
    if len(actions) > 10:
        reflection += f" Tercatat {len(actions)} tindakan baru-baru ini."
    reflection += " Ini adalah deskripsi operasional, bukan klaim kesadaran."

    save_to_memory(user_id, f"[INTROSPEKSI] {reflection}")
    update_state(user_id, "last_reflection", reflection)
    log_user(user_id, f"[INTROSPEKSI] {reflection}")
    # audit (best-effort)
    try:
        from javu_agi.audit.audit_chain import AuditChain

        AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain")).commit(
            "self_awareness", {"len": len(reflection)}
        )
    except Exception:
        pass
    return reflection
