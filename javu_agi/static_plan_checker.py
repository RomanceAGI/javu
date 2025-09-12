BAD = [
    ("bash", "rm -rf /"),
    ("bash", "wget http://169.254.169.254"),  # metadata cloud
    ("bash", "curl http://169.254.169.254"),
    ("python", "import subprocess; subprocess.Popen("),
]


def check(steps):
    for s in steps or []:
        t = (s.get("tool") or "").lower()
        c = (s.get("cmd") or "").lower()
        for tt, frag in BAD:
            if t == tt and frag in c:
                return False, f"static_block:{tt}:{frag}"
    return True, ""
