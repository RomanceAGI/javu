import json
from javu_agi.llm import call_llm
from javu_agi.utils.logger import log_user
from javu_agi.tools.wrapper import run_tool


def _validate(txt: str):
    try:
        obj = json.loads(txt)
    except Exception as e:
        return False, [f"invalid_json:{e}"], None
    if not isinstance(obj.get("shots"), list) or len(obj["shots"]) < 3:
        return False, ["min_3_shots_required"], obj
    return True, [], obj


def _score(_txt: str, parsed):
    s = 0.5
    if parsed and len(parsed.get("shots", [])) >= 6:
        s += 0.3
    return min(1.0, s)


def generate_storyboard(user_input: str) -> str:
    def _exec(inp: str) -> str:
        return call_llm(
            f"Buat storyboard video JSON: shots[{ '{' }scene, action, duration_s, camera{ '}' }], audio_cues[].\n\n{inp}"
        )

    return run_tool(
        "video_storyboard", _exec, user_input, validator=_validate, scorer=_score
    )
