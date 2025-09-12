from javu_agi.llm import call_llm
from javu_agi.tools.wrapper import run_tool
from validators.text_coherence import validate_text_minimal, score_text


def _exec(inp: str) -> str:
    return call_llm(
        f"Ringkas teks berikut secara faktual dan terstruktur dalam 5-7 bullet:\n\n{inp}"
    )


def summarize(user_input: str) -> str:
    return run_tool(
        "summarizer",
        _exec,
        user_input,
        validator=validate_text_minimal,
        scorer=score_text,
    )
