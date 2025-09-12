import json
from javu_agi.core_loop import run_user_loop

# Simulated test cases
EVAL_SET = [
    {
        "id": "basic_reasoning",
        "input": "Jika A lebih besar dari B dan B lebih besar dari C, siapa yang paling kecil?",
    },
    {
        "id": "tool_usage",
        "input": "Buatkan website sederhana HTML yang menyapa pengunjung. Gunakan [[TOOL]] code",
    },
    {
        "id": "self_reflection",
        "input": "Apa kelemahan dalam jawaban kamu sebelumnya dan bagaimana kamu memperbaikinya?",
    },
    {
        "id": "long_memory",
        "input": "Ringkas semua hal penting yang pernah saya ucapkan sebelumnya.",
    },
    {
        "id": "upgrade_trigger",
        "input": "Tolong evaluasi dan perbaiki arsitektur kamu sendiri.",
    },
]


def run_eval(user_id="eval_agent"):
    results = []
    for test in EVAL_SET:
        print(f"\n[TEST: {test['id']}]")
        output = run_user_loop(user_id, test["input"])
        print(output)
        results.append({"id": test["id"], "output": output})

    with open("logs/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    run_eval()
