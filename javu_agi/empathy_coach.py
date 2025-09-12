from javu_agi.llm_router import route_and_generate


def add_empathy(text: str) -> str:
    prompt = f"Rewrite with empathy, care, pro-human tone. Facts intact.\n\n{text}"
    try:
        r = route_and_generate(
            model=None,
            prompt=prompt,
            intent="empathy",
            temperature=0.3,
            distill_log=False,
        )
        out = (r or {}).get("text") or text
    except Exception:
        out = text
    return out[:1200]
