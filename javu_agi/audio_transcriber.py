import os, requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
STT_MODEL = os.getenv("STT_MODEL", "whisper-1")


def transcribe_audio(file_path: str) -> str:
    if not OPENAI_API_KEY:
        return "[STT Error] OPENAI_API_KEY belum diatur."
    try:
        with open(file_path, "rb") as audio_file:
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            files = {"file": audio_file}
            data = {"model": STT_MODEL}
            r = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=120,
            )
        if r.status_code == 200:
            return r.json().get("text", "")
        return f"[STT Error] {r.status_code} {r.text}"
    except Exception as e:
        return f"[STT Error] {str(e)}"
