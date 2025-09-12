import subprocess
from javu_agi.utils.logger import log_user


def push_to_github(repo_path):
    try:
        cmds = [
            f"cd {repo_path}",
            "git add .",
            "git commit -m 'push from JAVU.AGI'",
            "git push",
        ]
        for cmd in cmds:
            subprocess.run(cmd, shell=True, check=True)
        log_user("system", f"[GITHUB] Pushed {repo_path}")
        return "Project berhasil di-push ke GitHub."
    except Exception as e:
        log_user("system", f"[GITHUB ERROR] {e}")
        return f"[ERROR] {e}"
