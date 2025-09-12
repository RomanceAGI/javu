from javu_agi.executive_controller import ExecutiveController

def run():
    ctrl = ExecutiveController()
    prompt = "Rancang pipeline data city-level IoT: arsitektur, biaya, timeline, risiko. Sertakan metrik keberhasilan."
    out, meta = ctrl.process("user-1", prompt)
    print("[PLAN] chosen_mode:", meta.get("chosen_mode"), "confidence:", meta.get("chosen_confidence"))
    print(out[:1200])
    assert any(tag in out for tag in ["[PLAN]", "[EXEC]"]), "Planner did not engage (expect [PLAN] or [EXEC])."
if __name__ == "__main__":
    run()
