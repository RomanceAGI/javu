import subprocess, tempfile, os, signal


class SandboxError(Exception):
    pass


class ExecutionSandbox:
    def __init__(self, timeout=5):
        self.timeout = timeout

    def run(self, cmd: list[str], input_data: str = None) -> str:
        """Run command safely in isolated subprocess"""
        try:
            with tempfile.TemporaryFile() as tf:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=tf,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid,  # isolate process group
                )
                try:
                    out, _ = proc.communicate(
                        input=input_data.encode() if input_data else None,
                        timeout=self.timeout,
                    )
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    raise SandboxError("Execution timeout")
                tf.seek(0)
                return tf.read().decode(errors="ignore")
        except Exception as e:
            raise SandboxError(str(e))
