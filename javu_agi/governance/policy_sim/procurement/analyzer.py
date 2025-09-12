import statistics as stats


def zscores(xs):
    m = stats.mean(xs)
    s = max(1e-9, stats.pstdev(xs))
    return [(x - m) / s for x in xs]


def anomaly_contracts(contracts):
    # contracts: [{"vendor":"A","amount":100,"items":5,"days":7},...]
    amts = [c["amount"] for c in contracts]
    zs = zscores(amts)
    out = []
    for c, z in zip(contracts, zs):
        flags = []
        if z > 2.5:
            flags.append("amount_outlier")
        if c.get("days", 0) < 2 and c["amount"] > 50_000:
            flags.append("rush_large")
        out.append({**c, "flags": flags, "z": z})
    return sorted(out, key=lambda x: (len(x["flags"]), x["z"]), reverse=True)
