import subprocess
from javu_agi.utils.logger import log


def run_shell_command(command: str):
    try:
        result = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, timeout=10
        )
        output = result.decode("utf-8")
        log(f"[SHELL] {command} → {output}")
        return output
    except Exception as e:
        log(f"[SHELL ERROR] {e}")
        return str(e)
    if any(danger in command for danger in ["rm ", "shutdown", "kill"]):
        log(f"[BLOCKED] Dangerous command: {command}")
        return "[ERROR] Command blocked"
