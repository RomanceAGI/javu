import os, json, time, urllib.request, subprocess

WEBHOOK=os.getenv("NOTIFY_WEBHOOK","")

def send(evt, payload):
    if not WEBHOOK: return
    try:
        req=urllib.request.Request(WEBHOOK, data=json.dumps({"event":evt,"payload":payload}).encode("utf-8"),
                                   headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req, timeout=2)
    except Exception: pass

def check():
    r = subprocess.check_output(["./scripts/eval_gate.py"]).decode("utf-8")
    J = json.loads(r)
    gate = J["gate"]
    if not gate.get("pii_secret_ok", True):
        send("ALERT_PII_OR_SECRET", J)
    if not gate.get("exec_errors_ok", True):
        send("ALERT_EXEC_ERRORS", J)

if __name__=="__main__":
    while True:
        try: check()
        except Exception: pass
        time.sleep(300)  # 5 menit
