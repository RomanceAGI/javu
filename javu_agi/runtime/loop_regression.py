from javu_agi.core_loop import run_user_loop
import json
import os

TEST_GOALS = [
    "Buat daftar 3 ide aplikasi AI yang belum pernah ada.",
    "Identifikasi masalah etis dalam penggunaan LLM.",
    "Rancang strategi belajar untuk menjadi AGI researcher.",
    "Buat tool untuk menganalisis sentimen dari berita.",
    "Evaluasi kelemahan dalam struktur reasoning kamu.",
]

RESULTS_PATH = "logs/regression_results.json"


def run_tests():
    results = []
    user_id = "regression_agent"
    for idx, goal in enumerate(TEST_GOALS):
        print(f"\n🧪 [REGRESSION {idx}] {goal}")
        output = run_user_loop(user_id, goal)
        print(output)
        results.append({"goal": goal, "output": output})

    os.makedirs("logs", exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    run_tests()
