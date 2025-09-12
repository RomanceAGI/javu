from javu_agi.identity_model import get_identity


def check_constraints(text: str) -> list:
    violations = []
    identity = get_identity()
    constraints = identity.get("design_constraints", [])
    for rule in constraints:
        if rule.lower() not in text.lower():
            violations.append(f"⚠️ Kemungkinan pelanggaran: {rule}")
    return violations


def enforce_constraints(output: str) -> str:
    violations = check_constraints(output)
    if violations:
        annotated = output + "\n\n" + "\n".join(violations)
        return annotated
    return output
