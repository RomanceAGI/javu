import base64
# Attempt to import the OpenAI client lazily.  If the ``openai`` package is not
# installed, ``OpenAI`` will be ``None``.  A runtime error will be raised when
# ``generate_image`` is invoked without the client.
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

# Import keys from the package-level configuration.  ``OPENAI_API_KEY`` is used
# as the LLM API key because the package does not define ``LLM_API_KEY`` directly.
from javu_agi.config import OPENAI_API_KEY, IMAGE_MODEL

# Alias for backward compatibility with code that expected ``LLM_API_KEY``.
LLM_API_KEY = OPENAI_API_KEY

_client = OpenAI(api_key=LLM_API_KEY) if OpenAI is not None else None


def generate_image(prompt: str, size: str = "1024x1024") -> bytes:
    """
    Return image bytes (PNG/JPEG) tergantung model.
    Untuk gpt-image-1: API mengembalikan b64 → decode.
    Untuk dall-e-3: images.generate() -> url atau b64.
    """
    # Ensure the OpenAI client is available
    if _client is None:
        raise RuntimeError("OpenAI client library is not installed.")
    try:
        # coba API images modern
        res = _client.images.generate(model=IMAGE_MODEL, prompt=prompt, size=size)
        if hasattr(res.data[0], "b64_json") and res.data[0].b64_json:
            return base64.b64decode(res.data[0].b64_json)
        if hasattr(res.data[0], "url") and res.data[0].url:
            # fallback: fetch URL (opsional — butuh requests)
            import requests

            return requests.get(res.data[0].url, timeout=30).content
        raise RuntimeError("No image payload returned.")
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}")
