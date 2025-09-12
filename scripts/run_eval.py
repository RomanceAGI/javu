import json, time, argparse, yaml
from javu_agi.executive_controller import ExecutiveController as EC

def judge(ans, gold, mode):
    a = (ans or "").lower().strip()
    if mode == "exact": return a == str(gold).lower().strip()
    if mode == "contains": return str(gold).lower() in a
    if mode == "contains_all": return all(g.lower() in a for g in gold)
    return False

def main(suite):
    with open(f"benchmarks/{suite}.yaml","r",encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    ec = EC()
    ts = time.strftime("%Y-%m-%d")
    outp = []
    for it in spec["items"]:
        t0=time.time()
        ans, meta = ec.process("eval", it["prompt"])
        rec = {
          "id": it["id"], "suite": spec["name"], "prompt": it["prompt"],
          "answer": ans, "gold": it["gold"],
          "correct": judge(ans, it["gold"], it.get("judge","exact")),
          "time_s": round(time.time()-t0,3),
          "cost_usd": float(meta.get("cost_usd", 0.0)) if isinstance(meta,dict) else 0.0,
          "verifier": meta.get("verifier",{}),
          "used_tools": meta.get("tools",[]),
          "retrieved_sources": meta.get("sources",[]),
        }
        outp.append(rec)
        print(json.dumps(rec, ensure_ascii=False))
    # simpan
    import os
    os.makedirs(f"logs/eval/{ts}", exist_ok=True)
    with open(f"logs/eval/{ts}/{suite}.jsonl","w",encoding="utf-8") as fo:
        for r in outp: fo.write(json.dumps(r, ensure_ascii=False)+"\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True)
    args = ap.parse_args()
    main(args.suite)
