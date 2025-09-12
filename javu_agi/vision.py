from openai import OpenAI
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
_client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_image_with_llm(
    image_url: str, question: str = "Apa isi gambar ini?"
) -> str:
    """
    Pakai model vision (4o/5) via chat.completions format image_url.
    """
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o",  # router belum untuk media payload; set 4o vision-safe
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[VISION ERROR] {str(e)}"
