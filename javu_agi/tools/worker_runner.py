import os, subprocess, shlex, resource, signal, re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ALLOWED = {"python", "jq"}  # ketat
TIMEOUT = int(os.getenv("WORKER_TIMEOUT", "8"))
MAX_OUT = 64 * 1024  # 64KB
MAX_CMD = 8000
DENY_CHARS = set("`$(){}[]|;&><\\")
DENY_RE = [
    re.compile(p, re.I)
    for p in [
        r"\b(rm\s+-rf|mkfs|mount|umount|shutdown|reboot|halt)\b",
        r"/etc/passwd|/etc/shadow",
        r"ssh\s+|scp\s+|sftp\s+|curl\s+|wget\s+|http[s]?://",
    ]
]


class Job(BaseModel):
    cmd: str
    input_text: str | None = None


from javu_agi.security.sandbox import run as sandbox_run


def run_shell(cmd: str):
    wd = os.getenv("EP_WORKDIR", "")
    if wd:
        os.chdir(wd)
    cpu = int(os.getenv("SANDBOX_CPU_SECS", "5"))
    mem = int(os.getenv("SANDBOX_MEM_MB", "512"))
    mem = int(os.getenv("SANDBOX_MEM_MB", "512"))
    nonet = os.getenv("SANDBOX_NO_NET", "1") == "1"
    nproc = int(os.getenv("SANDBOX_NPROC", "64"))
    nonet = os.getenv("SANDBOX_NO_NET", "1") == "1"
    tout = int(os.getenv("TOOL_TIMEOUT_S", "30"))
    return sandbox_run(
        cmd,
        timeout_s=int(os.getenv("TOOL_TIMEOUT_S", "30")),
        cpu_sec=cpu,
        mem_mb=mem,
        nproc=nproc,
        no_net=nonet,
    )


app = FastAPI(title="tool-worker")


def _limit():
    # CPU time ~ 2s, address space ~ 512MB, no core dumps
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _clean_env():
    return {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C", "NO_COLOR": "1"}


def _validate(cmd: str):
    if not isinstance(cmd, str) or len(cmd) > MAX_CMD:
        raise HTTPException(400, "bad cmd length")
    parts = shlex.split(cmd)
    if not parts:
        raise HTTPException(400, "empty cmd")
    if parts[0] not in ALLOWED:
        raise HTTPException(403, "tool not allowed")
    if any(c in DENY_CHARS for c in cmd):
        raise HTTPException(403, "forbidden shell meta-chars")
    for rx in DENY_RE:
        if rx.search(cmd):
            raise HTTPException(403, "denied pattern")
    return parts


@app.post("/run")
def run(j: Job):
    parts = _validate(j.cmd)
    try:
        p = subprocess.Popen(
            parts,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=_limit,
            env=_clean_env(),
        )
        out, err = p.communicate(
            input=(j.input_text or "").encode("utf-8"), timeout=TIMEOUT
        )
        out = out[:MAX_OUT]
        err = err[:MAX_OUT]
        return {
            "code": p.returncode,
            "stdout": out.decode("utf-8", "ignore"),
            "stderr": err.decode("utf-8", "ignore"),
        }
    except subprocess.TimeoutExpired:
        p.kill()
        return {"code": 124, "stdout": "", "stderr": "timeout"}
