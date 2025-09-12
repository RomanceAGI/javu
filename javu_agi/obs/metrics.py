from prometheus_client import Counter, Histogram, Gauge


class M:
    # reasoning
    reqs = Counter("agi_requests_total", "Total cognition requests", ["mode", "status"])
    latency = Histogram("agi_latency_seconds", "End-to-end latency", ["mode"])
    # cognition signals
    uncertainty = Histogram("agi_uncertainty", "Estimated uncertainty")
    reward = Histogram("agi_reward", "Shaped reward")
    confidence = Histogram("agi_confidence", "Simulated confidence")
    # memory/rag
    recall_hits = Gauge("agi_recall_hits", "Recall hits (semantic+episodic)")
