from javu_agi.llm import call_llm
from javu_agi.utils.logger import log_user
from validators.unity_checker import static_sanity, roslyn_compile_check, quality_score
from quality.score import log_quality

_DENY = {"cheat", "aimbot", "wallhack", "keylogger", "ransomware"}


def _validate(code: str):
    warns = static_sanity(code) + roslyn_compile_check(code)
    return (len(warns) == 0), warns, None


def generate_unity_script(user_input: str) -> str:
    def _exec(inp: str) -> str:
        return call_llm(
            f"Tulis skrip Unity C# (namespace Generated, public class, Start/Update bila relevan). Compile-ready.:\n\n{inp}"
        )

    return run_tool(
        "unity_script", _exec, user_input, validator=_validate, scorer=quality_score
    )
