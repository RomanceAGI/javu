from __future__ import annotations
import os, socket, ipaddress
from typing import Iterable

LOCAL_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
]
BLOCK_HOSTS = {"localhost", "0.0.0.0", "::1", "metadata.google.internal"}
BLOCK_IPS = {"169.254.169.254"}  # cloud metadata

SAFE_ENV_ALLOWLIST = {
    "PATH",
    "PYTHONPATH",
    "PYTHONUNBUFFERED",
    "TZ",
    "LANG",
    "API_KEYS",
    "ADMIN_KEYS",
    "EGRESS_ALLOWLIST",
    # tambahkan var aman lo di sini
}


def preflight():
    # 1) egress allowlist: pastikan tidak ada loopback/metadata
    al = (os.getenv("EGRESS_ALLOWLIST", "") or "").split(",")
    for host in al:
        h = host.strip().lower()
        if not h:
            continue
        if h in BLOCK_HOSTS:
            raise RuntimeError(f"Unsafe allowlist host: {h}")
        try:
            ip = socket.gethostbyname(h)
            ipaddr = ipaddress.ip_address(ip)
            if any(ipaddr in n for n in LOCAL_NETS) or ip in BLOCK_IPS:
                raise RuntimeError(f"Unsafe resolved host: {h} -> {ip}")
        except Exception:
            # jika gagal resolve di startup, abaikan (akan dicek saat tool_contracts allow_hosts)
            pass

    # 2) env vars: sembunyikan secrets di luar allowlist (opsional)
    if os.getenv("SANDBOX_STRIP_ENV", "1") == "1":
        for k in list(os.environ.keys()):
            if (
                k not in SAFE_ENV_ALLOWLIST
                and not k.endswith("_ACCESS_TOKEN")
                and not k.endswith("_REFRESH_TOKEN")
            ):
                try:
                    del os.environ[k]
                except Exception:
                    pass

    return True
