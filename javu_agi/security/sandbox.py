import os, resource, signal, subprocess


def _preexec(cpu_sec=5, mem_mb=512, nproc=64, no_net=False):
    def fn():
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_sec, cpu_sec))
            resource.setrlimit(
                resource.RLIMIT_AS, (mem_mb * 1024 * 1024, mem_mb * 1024 * 1024)
            )
            resource.setrlimit(resource.RLIMIT_NPROC, (nproc, nproc))
            resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
            os.umask(0o077)
            os.setsid()
            # optional: block networking via env flag checked by worker
            if no_net:
                os.environ["SANDBOX_NO_NET"] = "1"
        except Exception:
            pass

    return fn


def run(cmd: str, timeout_s=30, cpu_sec=5, mem_mb=512, nproc=64, no_net=True):
    try:
        p = subprocess.Popen(
            ["/bin/bash", "-lc", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=_preexec(cpu_sec, mem_mb, nproc, no_net),
            text=True,
            env={
                k: v
                for k, v in os.environ.items()
                if k
                not in (
                    "AWS_SECRET_ACCESS_KEY",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "ELEVENLABS_API_KEY",
                )
            },
        )
        try:
            out, err = p.communicate(timeout=timeout_s)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
            return {"code": 124, "stdout": "", "stderr": "[TIMEOUT]"}
        return {"code": p.returncode, "stdout": out or "", "stderr": err or ""}
    except Exception as e:
        return {"code": -1, "stdout": "", "stderr": f"[SANDBOX_ERROR] {e}"}
