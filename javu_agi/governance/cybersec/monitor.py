import re, json, time


def parse_syslog(lines):
    alerts = []
    for ln in lines:
        if "sudo" in ln and "FAIL" in ln:
            alerts.append({"kind": "auth_fail", "ln": ln})
        if "iptables" in ln and "DROP" in ln:
            alerts.append({"kind": "fw_drop", "ln": ln})
    return alerts


def risk_score(alerts):
    w = {"auth_fail": 2.0, "fw_drop": 0.5}
    return sum(w.get(a["kind"], 0.1) for a in alerts)


def summarize(alerts):
    kinds = {}
    for a in alerts:
        kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
    return {"counts": kinds, "score": risk_score(alerts)}
