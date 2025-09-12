from javu_agi.auto_module_generator import generate_and_save_module


def analyze_internal_limitations(logs: list[str]) -> list[str]:
    return [
        log
        for log in logs
        if any(k in log.lower() for k in ["gagal", "kesalahan", "tidak bisa"])
    ]


def propose_architecture_modifications(limitations: list[str]) -> list[str]:
    return [f"Solusi arsitektur untuk: {l}" for l in limitations]


def perform_self_upgrade(user_id: str, logs: list[str], memory: list[str]) -> list[str]:
    limitations = analyze_internal_limitations(logs)
    if not limitations:
        return []

    upgrades = propose_architecture_modifications(limitations)
    created = []

    for upgrade in upgrades:
        mod_name = generate_and_save_module(upgrade)
        memory.append(f"[SELF-UPGRADE] Modul: {mod_name} untuk {upgrade}")
        created.append(mod_name)

    return created
