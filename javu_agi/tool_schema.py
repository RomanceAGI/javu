from javu_agi.llm import call_llm
from javu_agi.tools.wrapper import run_tool
from validators.json_validator import validate_flow_json


def _score(_txt: str, parsed):  # pakai jumlah screens sebagai proxy
    s = 0.5
    if parsed:
        if len(parsed.get("screens", [])) >= 5:
            s += 0.3
        if len(parsed.get("data_models", [])) >= 3:
            s += 0.1
    return min(1.0, s)


def generate_schema(user_input: str) -> str:
    def _exec(inp: str) -> str:
        return call_llm(
            f"Bangun skema aplikasi JSON dgn kunci [screens,actions,data_models]:\n\n{inp}"
        )

    return run_tool(
        "schema_gen", _exec, user_input, validator=validate_flow_json, scorer=_score
    )
