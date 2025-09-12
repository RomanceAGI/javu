import os
import tempfile
import requests
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("TTS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# 🎙️ Rekam suara user selama x detik
def record_audio(seconds=5, fs=44100):
    print("🎤 [Mendengarkan]...")
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        wav.write(f.name, fs, recording)
        return f.name


# 🔊 Suarakan respon pakai ElevenLabs
def speak_text(text):
    if not ELEVENLABS_API_KEY:
        print("[TTS Error] API Key belum diatur.")
        return
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "accept": "audio/mpeg",
    }
    data = {"text": text, "model_id": "eleven_monolingual_v1"}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(response.content)
            os.system(f"mpg123 {f.name}")
    else:
        print("[TTS Error]", response.text)


# 🔎 Ubah suara ke teks via Whisper API
def transcribe_audio(file_path):
    if not OPENAI_API_KEY:
        print("[STT Error] OPENAI_API_KEY belum diatur.")
        return ""
    with open(file_path, "rb") as audio_file:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        files = {"file": audio_file}
        data = {"model": "whisper-1"}
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
        )
        if response.status_code == 200:
            return response.json().get("text", "")
        else:
            print("[STT Error]", response.text)
            return ""
