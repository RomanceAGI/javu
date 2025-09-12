from javu_agi.memory.memory import recall_from_memory


def reason_about_cause(user_id, situation):
    context = recall_from_memory(user_id, situation)
    triggers = ["gagal", "tidak berhasil", "error", "konflik"]
    if any(trigger in context.lower() for trigger in triggers):
        return "Kemungkinan penyebab: strategi sebelumnya tidak sesuai konteks."
    return "Penyebab belum jelas, perlu observasi lebih lanjut."
