import os, threading, time
from wsgiref.simple_server import make_server

_METRICS = {
    "arena_success": 0.0,
    "transfer_success": 0.0,
    "adversarial_success": 0.0,
    "req_qps": 0.0,
    "lat_ms": 0.0,
}

_LOCK = threading.Lock()


def set_metric(name: str, value: float):
    with _LOCK:
        _METRICS[name] = float(value)


def inc_metric(name: str, delta: float = 1.0):
    with _LOCK:
        _METRICS[name] = float(_METRICS.get(name, 0.0) + delta)


def _app(environ, start_response):
    if environ.get("PATH_INFO") != "/metrics":
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"not found"]
    lines = []
    with _LOCK:
        for k, v in _METRICS.items():
            lines.append(f"{k} {v}")
    body = ("\n".join(lines) + "\n").encode()
    start_response("200 OK", [("Content-Type", "text/plain; version=0.0.4")])
    return [body]


def serve(host="0.0.0.0", port=9200, daemon=True):
    httpd = make_server(host, port, _app)
    t = threading.Thread(target=httpd.serve_forever, daemon=daemon)
    t.start()
    return t


if __name__ == "__main__":
    host = os.getenv("METRICS_HOST", "0.0.0.0")
    port = int(os.getenv("METRICS_PORT", "9200"))
    serve(host, port, daemon=False)
if "merged_reasoning" in results:
    set_metric("multimodal_reasoning_length", len(results["merged_reasoning"]))
if "image" in results:
    set_metric("multimodal_image_generated", 1)
if "audio" in results:
    set_metric("multimodal_audio_generated", 1)
if "video" in results:
    set_metric("multimodal_video_generated", 1)
