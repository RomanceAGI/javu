import socket, yaml

AL = yaml.safe_load(open("governance/policies/egress_allowlist.yaml"))["domains"]


def check_host(host):
    return any(host.endswith(d) for d in AL)


def guarded_connect(host, *a, **k):
    if not check_host(host):
        raise PermissionError(f"Egress blocked: {host}")
    return socket.create_connection((host, *a), **k)
