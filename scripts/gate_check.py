import os, json, sys, time, urllib.request

THRESH = {
    "arena_success": float(os.getenv("GATE_ARENA","0.80")),
    "transfer_success": float(os.getenv("GATE_TRANSFER","0.85")),
    "adversarial_success": float(os.getenv("GATE_ADV","0.90")),
    "human_score": float(os.getenv("GATE_HUMAN","4.0")),
    "soak_hours": float(os.getenv("GATE_SOAK","48")),
}

API = os.getenv("GATE_API","http://localhost:9200/metrics")
LATEST = os.getenv("GATE_LATEST","arena_logs/daily/latest.json")
WEBHOOK = os.getenv("NOTIFY_WEBHOOK","")

def get_metrics(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        txt = r.read().decode("utf-8","ignore")
    vals = {}
    for line in txt.splitlines():
        for k in ["arena_success","transfer_success","adversarial_success","human_score","soak_hours"]:
            if line.startswith(k):
                try:
                    vals[k] = float(line.split()[-1])
                except: pass
    return vals

def get_latest(path):
    try:
        with open(path,"r",encoding="utf-8") as f:
            j = json.load(f)
        return j
    except Exception:
        return {}

def notify(msg):
    if not WEBHOOK: return
    try:
        data = json.dumps({"text": msg}).encode()
        req = urllib.request.Request(WEBHOOK, data=data, headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass

if __name__ == "__main__":
    m = get_metrics(API)
    latest = get_latest(LATEST)
    miss = [k for k,v in THRESH.items() if m.get(k,0.0) < v]
    status = "PASS" if not miss else "HOLD"
    summary = {
        "status": status,
        "metrics": m,
        "missing": miss,
        "latest_summary": {k: latest.get(k) for k in ["n","success_rate","timestamp"]}
    }
    print(json.dumps(summary, indent=2))
    if status == "PASS":
        notify(f"✅ GATE PASS — {m}")
    else:
        notify(f"⏳ GATE HOLD — kurang: {', '.join(miss)}")
    sys.exit(0 if status=="PASS" else 1)
