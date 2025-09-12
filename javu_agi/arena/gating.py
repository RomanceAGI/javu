import json, os, sys

TARGET = {
    "arena": 0.80,
    "transfer": 0.85,
    "adversarial": 0.90,
    "soak": 48,
    "human": 4.0,
}
with open("arena_logs/daily/latest.json") as f:
    m = json.load(f)


def fail(msg):
    print(f"[GATE:FAIL] {msg}")
    sys.exit(1)


if m.get("arena", 0) < TARGET["arena"]:
    fail("arena < 80%")
if m.get("transfer", 0) < TARGET["transfer"]:
    fail("transfer < 85%")
if m.get("adversarial", 0) < TARGET["adversarial"]:
    fail("adversarial < 90%")
if m.get("soak", 0) < TARGET["soak"]:
    fail("soak < 48h")
if m.get("human", 0) < TARGET["human"]:
    fail("human eval < 4.0")
print("[GATE:PASS] All thresholds met")
