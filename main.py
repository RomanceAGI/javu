from __future__ import annotations
import os, sys, signal, time, logging
from pathlib import Path

from javu_agi.agi_manager import start_all_instances, stop_all_instances
from javu_agi.config import assert_keys, export_router_context
from javu_agi.audit.audit_chain import AuditChain
from javu_agi.transparency_reporter import TransparencyReporter
from javu_agi.api_server import run_health_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("main")
_audit = AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain"))
_transparency = TransparencyReporter(output_dir=os.getenv("TRANSPARENCY_DIR", "logs/transparency"))

def _graceful_shutdown(signum, frame):
    log.warning("Shutdown signal received (sig=%s). Stopping all instances...", signum)
    try:
        stop_all_instances()
        _audit.commit("system:shutdown", {"sig": signum})
        _transparency.record("shutdown", {"sig": signum, "ts": time.time()})
    except Exception as e:
        log.error("Error during shutdown: %s", e)
    sys.exit(0)

def main():
    log.info("🚀 JAVU.AGI FULL SYSTEM STARTING...")

    # Preflight: cek API keys & env
    missing = assert_keys()
    if missing:
        log.error("Missing required keys: %s", missing)
        sys.exit(1)

    # Router context preview
    ctx = export_router_context()
    log.info("Router context: %s", ctx)

    # Register shutdown hooks
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # Start
    try:
        start_all_instances()
        _audit.commit("system:start", {"pid": os.getpid()})
        _transparency.record("startup", {"pid": os.getpid(), "ctx": ctx})
    except Exception as e:
        log.exception("Fatal during startup: %s", e)
        sys.exit(1)

    # Keep alive
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        _graceful_shutdown(signal.SIGINT, None)

if __name__ == "__main__":
    main()
