import subprocess
import pyautogui
import time

def execute_action(action: str):
    print(f"[ACTION] Eksekusi: {action}")

    try:
        if action.startswith("type:"):
            content = action.split("type:")[1].strip()
            pyautogui.write(content, interval=0.05)
        elif action.startswith("open:"):
            app = action.split("open:")[1].strip()
            subprocess.Popen(app)
        elif action.startswith("delay:"):
            duration = float(action.split("delay:")[1].strip())
            time.sleep(duration)
        else:
            print(f"[ACTION] Tidak dikenali: {action}")
    except Exception as e:
        print(f"[ACTION ERROR] {e}")
