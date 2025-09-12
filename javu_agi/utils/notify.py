from __future__ import annotations
import os, sys, json, time, urllib.request

# --- env webhooks ---
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")
TEAMS_WEBHOOK = os.getenv("TEAMS_WEBHOOK", "")
GENERIC_WEBHOOK = os.getenv("NOTIFY_WEBHOOK", "")  # generic


def _http_post(url: str, payload: dict, timeout: int = 5) -> bool:
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status) in (200, 204)
    except Exception:
        return False


def _stdout(event: str, payload: dict) -> None:
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sys.stdout.write(
        json.dumps({"t": t, "event": event, "payload": payload or {}}) + "\n"
    )
    sys.stdout.flush()


# --- legacy-compatible: text message ---
def send(text: str, channel: str | None = None) -> bool:
    """
    Kirim pesan singkat. Prioritas: Slack > Discord > Teams > Generic.
    channel (opsional) hanya dipakai Slack (kalau webhook mendukung).
    """
    body = {"text": text}
    if SLACK_WEBHOOK:
        if channel:
            body = {"text": text, "channel": channel}
        if _http_post(SLACK_WEBHOOK, body):
            return True
    if DISCORD_WEBHOOK:
        if _http_post(DISCORD_WEBHOOK, {"content": text}):
            return True
    if TEAMS_WEBHOOK:
        # Teams expects 'text' is fine for simple connector cards
        if _http_post(TEAMS_WEBHOOK, {"text": text}):
            return True
    if GENERIC_WEBHOOK:
        if _http_post(
            GENERIC_WEBHOOK, {"event": "notify.text", "payload": {"text": text}}
        ):
            return True
    # fallback
    _stdout("notify.text", {"text": text})
    return False


# --- structured event ---
def notify(event: str, payload: dict) -> None:
    """
    Event terstruktur. Coba kirim ke webhook yang tersedia, lalu fallback stdout.
    """
    posted = False
    body = {"event": event, "payload": payload or {}}

    if SLACK_WEBHOOK:
        # Slack basic payload
        txt = f"*{event}*\n```{json.dumps(payload or {}, ensure_ascii=False)}```"
        posted = _http_post(SLACK_WEBHOOK, {"text": txt}) or posted
    if DISCORD_WEBHOOK:
        posted = (
            _http_post(
                DISCORD_WEBHOOK,
                {
                    "content": f"**{event}**\n```json\n{json.dumps(payload or {}, ensure_ascii=False)}\n```"
                },
            )
            or posted
        )
    if TEAMS_WEBHOOK:
        posted = (
            _http_post(
                TEAMS_WEBHOOK,
                {"text": f"{event}\n{json.dumps(payload or {}, ensure_ascii=False)}"},
            )
            or posted
        )
    if GENERIC_WEBHOOK:
        posted = _http_post(GENERIC_WEBHOOK, body) or posted

    if not posted:
        _stdout(event, payload or {})


def notify_gating_pass(metrics: dict):
    msg = f"✅ GATE PASS: {metrics}"
    return send(msg)


def notify_gating_fail(reason: str, metrics: dict | None = None):
    msg = f"❌ GATE FAIL: {reason}\n{metrics or ''}"
    return send(msg)
