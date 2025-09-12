import json, os, time
from flask import Flask, jsonify


def create_portal(log_dir="artifacts/audit"):
    app = Flask(__name__)

    @app.route("/status")
    def status():
        return jsonify({"ts": int(time.time()), "status": "ok"})

    @app.route("/logs/<path:fname>")
    def logs(fname):
        path = os.path.join(log_dir, fname)
        if not os.path.isfile(path):
            return jsonify({"error": "not found"}), 404
        with open(path, "r", encoding="utf-8") as f:
            data = [json.loads(x) for x in f.readlines()[-200:]]
        return jsonify(data)

    @app.route("/eco")
    def eco():
        eco_file = os.path.join(log_dir, "eco_impact.jsonl")
        if not os.path.isfile(eco_file):
            return jsonify({"eco": "no data"})
        with open(eco_file, "r") as f:
            lines = [json.loads(x) for x in f.readlines()[-100:]]
        return jsonify(lines)

    return app
