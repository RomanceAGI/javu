from javu_agi.llm import call_llm
from javu_agi.tools.wrapper import run_tool
from validators.text_coherence import validate_text_minimal, score_text


def _exec(inp: str) -> str:
    return call_llm(
        f"Terjemahkan ke Bahasa Indonesia dengan akurat, pertahankan makna teknis:\n\n{inp}"
    )


def translate(user_input: str) -> str:
    return run_tool(
        "translator",
        _exec,
        user_input,
        validator=validate_text_minimal,
        scorer=score_text,
    )
