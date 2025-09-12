import json, sys, glob, statistics as st
fn = sys.argv[1]  # logs/eval/2025-08-17/reasoning.jsonl
rows = [json.loads(x) for x in open(fn,encoding="utf-8")]
acc = sum(1 for r in rows if r["correct"])/max(1,len(rows))
lat = st.median([r["time_s"] for r in rows])
cost= sum(r["cost_usd"] for r in rows)
print(json.dumps({"acc":round(acc,3),"p50_latency":lat,"cost_usd":round(cost,4)}))
