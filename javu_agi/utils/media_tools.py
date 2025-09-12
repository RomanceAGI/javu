import requests
import os


def elevenlabs_tts(text: str):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    url = "https://api.elevenlabs.io/v1/text-to-speech"
    resp = requests.post(url, headers={"xi-api-key": api_key}, json={"text": text})
    return resp.json().get("audio_url")


def runway_video_gen(prompt: str):
    api_key = os.getenv("RUNWAY_API_KEY")
    url = "https://api.runwayml.com/v1/videos"
    resp = requests.post(
        url, headers={"Authorization": f"Bearer {api_key}"}, json={"prompt": prompt}
    )
    return resp.json().get("video_url")
