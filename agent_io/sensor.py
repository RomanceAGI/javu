import keyboard

def observe_keyboard() -> str:
    print("[SENSOR] Tunggu input teks manual (Enter untuk kirim)...")
    try:
        text = input(">> ")
        return text
    except Exception as e:
        print("[SENSOR ERROR]", e)
        return ""
    # if keyboard.is_pressed("esc"):
#     return "[INTERRUPT]"
