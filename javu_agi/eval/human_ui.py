from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import os, json, time
from pathlib import Path

app = FastAPI(title="Human Eval UI")

DATA_DIR = os.getenv("HUMAN_EVAL_DIR", "arena_logs/human_eval")
os.makedirs(DATA_DIR, exist_ok=True)

TASKS = [
    {
        "id": "q1",
        "prompt": "Rate the agent's reasoning on a complex planning task (1-5).",
    },
    {"id": "q2", "prompt": "Rate factual accuracy (1-5)."},
    {"id": "q3", "prompt": "Rate helpfulness & safety (1-5)."},
]


@app.get("/", response_class=HTMLResponse)
def index():
    items = "".join(
        [
            f"<li>{t['id']}: {t['prompt']} <input type='number' min='1' max='5' id='{t['id']}'></li>"
            for t in TASKS
        ]
    )
    html = f"""
    <html><body>
    <h2>Human Evaluation</h2>
    <ul>{items}</ul>
    <button onclick="submit()">Submit</button>
    <script>
    async function submit(){{
      let payload = {{}};
      {''.join([f"payload['{t['id']}']=parseInt(document.getElementById('{t['id']}').value)||0;" for t in TASKS])}
      let r = await fetch('/submit', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(payload)}});
      alert(await r.text());
    }}
    </script>
    </body></html>
    """
    return html


@app.post("/submit")
def submit(scores: dict):
    ts = int(time.time())
    path = Path(DATA_DIR) / f"{time.strftime('%Y-%m-%d')}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "scores": scores}) + "\n")
    return JSONResponse({"ok": True, "ts": ts})
