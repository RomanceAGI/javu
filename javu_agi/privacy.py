memory_log = []

def log_action(action: str) -> None:
    """
    Append an action to the in-memory log, tagging it as sensitive when appropriate.

    If the action contains the keywords ``"password"`` or ``"akses rahasia"`` (secret access),
    the stored log entry will be prefixed with ``"[SENSITIVE] "``.  Otherwise the action is
    stored as-is.  All actions are appended exactly once.
    """
    lowered = action.lower()
    if "password" in lowered or "akses rahasia" in lowered:
        memory_log.append("[SENSITIVE] " + action)
    else:
        memory_log.append(action)

def get_log():
    return "\n".join(memory_log)

def revoke_access(area: str):
    return f"Akses ke {area} dinonaktifkan (simulasi)."
