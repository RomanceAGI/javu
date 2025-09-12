import os
import tempfile
from javu_agi.llm import call_llm
from javu_agi.media_router import generate_image
from javu_agi.utils.logger import log_user
from javu_agi.tools.wrapper import run_tool
from validators.text_coherence import validate_text_minimal, score_text


def _exec(inp: str) -> str:
    return call_llm(
        f"Buat prompt gambar (komposisi, gaya, lighting) dalam JSON field: subject, style, camera, mood, details.\n\n{inp}"
    )


def image_prompt(user_input: str) -> str:
    return run_tool(
        "image_prompt",
        _exec,
        user_input,
        validator=validate_text_minimal,
        scorer=score_text,
    )


def generate_image_file(
    user_input: str, size: str = "1024x1024", user_id: str = "system"
) -> str:
    img_bytes = generate_image(user_input, size=size)
    os.makedirs("artifacts", exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, dir="artifacts", suffix=".png")
    with open(tmp.name, "wb") as f:
        f.write(img_bytes)
    log_user(user_id, f"[IMAGE GEN] prompt='{user_input}' -> {tmp.name}")
    return tmp.name
