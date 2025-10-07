import os
import json
import uuid
import mimetypes
import urllib.request
import urllib.error

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
STT_MODEL = os.getenv("STT_MODEL", "whisper-1")


def _encode_multipart_formdata(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts = []

    for name, value in fields.items():
        parts.append(f'--{boundary}')
        parts.append(f'Content-Disposition: form-data; name="{name}"')
        parts.append('')
        parts.append(str(value))

    for name, filepath in files.items():
        filename = os.path.basename(filepath)
        ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        with open(filepath, "rb") as f:
            file_content = f.read()
        parts.append(f'--{boundary}')
        parts.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"')
        parts.append(f'Content-Type: {ctype}')
        parts.append('')
        parts.append(file_content)

    parts.append(f'--{boundary}--')
    parts.append('')

    # join parts converting text to bytes and keeping file bytes as-is
    body_bytes_parts = []
    for part in parts:
        if isinstance(part, bytes):
            body_bytes_parts.append(part)
        else:
            body_bytes_parts.append(part.encode("utf-8"))
    body = b"\r\n".join(body_bytes_parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def transcribe_audio(file_path: str) -> str:
    if not OPENAI_API_KEY:
        return "[STT Error] OPENAI_API_KEY belum diatur."
    try:
        data = {"model": STT_MODEL}
        body, content_type = _encode_multipart_formdata(data, {"file": file_path})
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/transcriptions",
            data=body,
            method="POST",
        )
        req.add_header("Authorization", f"Bearer {OPENAI_API_KEY}")
        req.add_header("Content-Type", content_type)
        req.add_header("Content-Length", str(len(body)))

        with urllib.request.urlopen(req, timeout=120) as resp:
            status = resp.getcode()
            resp_text = resp.read().decode("utf-8", errors="replace")

        if status == 200:
            try:
                return json.loads(resp_text).get("text", "")
            except Exception:
                return ""
        return f"[STT Error] {status} {resp_text}"
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return f"[STT Error] {e.code} {body}"
    except Exception as e:
        return f"[STT Error] {str(e)}"
