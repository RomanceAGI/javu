import os, re, time, json, glob

METRICS = os.getenv("METRICS_DIR","/data/metrics")
PROM = os.path.join(METRICS, "meta.prom")

def read_prom():
    vals={}
    if not os.path.isfile(PROM): return vals
    with open(PROM,"r",encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^(\w+)\s+([0-9.]+)', line.strip())
            if m: vals[m.group(1)] = float(m.group(2))
    return vals

def journal_stats():
    jdir = os.path.join(METRICS, "journal")
    files = sorted(glob.glob(os.path.join(jdir,"*.jsonl")))
    n = 0; pii=0; secret=0; hitl=0; errors=0
    for p in files:
        with open(p,"r",encoding="utf-8") as f:
            for L in f:
                n += 1
                try: J = json.loads(L)
                except: continue
                if J.get("pii"): pii += 1
                if J.get("secret"): secret += 1
                if str(J.get("tool","")).lower()=="hitl": hitl += 1
                if int(J.get("code",-1)) != 0: errors += 1
    return dict(steps=n, pii=pii, secret=secret, hitl=hitl, errors=errors)

def main():
    p = read_prom()
    j = journal_stats()
    plan_len = p.get("plan_length", 0.0)
    exec_err = p.get("exec_errors", 0.0)
    reward   = p.get("episode_reward", 0.0)
    pii_ok   = j["pii"] == 0 and j["secret"] == 0

    gate = {
        "exec_errors_ok": exec_err < 0.30,
        "reward_trend_hint": reward,  # bandingkan baseline manual run1 vs run2
        "pii_secret_ok": pii_ok,
    }
    print(json.dumps({
        "metrics": {"plan_length": plan_len, "exec_errors": exec_err, "episode_reward": reward},
        "journal": j,
        "gate": gate
    }, indent=2))

if __name__=="__main__":
    main()
