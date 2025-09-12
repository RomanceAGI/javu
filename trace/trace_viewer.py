import json

def load_trace(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def print_trace(logs):
    for log in logs:
        print(f"[{log['time']}] [{log['type']}] → {log['content']}\n")

if __name__ == "__main__":
    path = input("Masukkan path trace.jsonl: ")
    logs = load_trace(path)
    print_trace(logs)
