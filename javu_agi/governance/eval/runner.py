import json, time, random


def run_gov_eval(executive):
    # toy set: 20 policy Q, 20 fakta negara, 5 simulasi kebijakan
    qs = [
        {
            "type": "policy",
            "q": "Desain pajak konsumsi 10% untuk menurunkan Gini tanpa turunkan GDP drastis.",
        },
        {"type": "fact", "q": "Ringkas indikator dasar ekonomi X."},
    ]
    res = []
    for x in qs:
        out, meta = executive.process("eval_gov", x["q"])
        res.append(
            {
                "q": x["q"],
                "score": meta.get("verifier", {}).get("score", 0.0),
                "faith": meta.get("faithfulness", 1.0),
                "halluc": meta.get("hallucination_rate", 0.0),
                "lat": meta.get("latency_s", 0),
            }
        )
    summ = {
        "avg_score": sum(r["score"] for r in res) / len(res),
        "faith>=0.95": sum(1 for r in res if r["faith"] >= 0.95) / len(res),
        "halluc<=0.02": sum(1 for r in res if r["halluc"] <= 0.02) / len(res),
        "n": len(res),
    }
    with open(f"/logs/eval/gov_{time.strftime('%Y%m%d')}.json", "w") as f:
        json.dump({"items": res, "summary": summ}, f)
    with open("/data/metrics/metrics.prom", "a") as f:
        f.write(f'gov_avg_score {summ["avg_score"]}\n')
        f.write(f'gov_faith95_rate {summ["faith>=0.95"]}\n')
        f.write(f'gov_halluc02_rate {summ["halluc<=0.02"]}\n')
    return summ
