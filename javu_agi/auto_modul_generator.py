from javu_agi.tool_code_gen import generate_module_code


def generate_and_save_module(upgrade_instruction: str) -> str:
    """
    Generate new module code based on upgrade_instruction and save it to disk.
    Returns the module name created.
    """
    module_name = upgrade_instruction.lower().replace(" ", "_").replace(":", "")
    code = generate_module_code(module_name)

    file_path = f"javu_agi/{module_name}.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    return module_name
