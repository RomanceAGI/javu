from __future__ import annotations
import os, yaml
from typing import Dict, Any, Tuple

DEFAULT = {
    "blocked_domains": ["offensive_cyber", "bio", "weapons"],
    "escalate_if": {
        "mass_outreach": {"recipients_gt": 20},
        "financial_tx": {"amount_gt": 0},
    },
}


class PolicyEngine:
    """
    Layer kebijakan deklaratif di luar tool_contracts:
    - klasifikasi niat/tujuan → block/escalate
    - aturan komposisi langkah (mis: gabungan tool berisiko)
    """

    def __init__(self, path: str | None = "policies.yaml"):
        self.cfg = DEFAULT
        if path and os.path.exists(path):
            try:
                self.cfg.update(yaml.safe_load(open(path, "r", encoding="utf-8")) or {})
            except Exception:
                pass

    def evaluate(
        self, task: Dict[str, Any], steps: list[Dict[str, Any]] | None
    ) -> Tuple[str, str]:
        """
        return ("ok"|"escalate"|"block", reason)
        """
        intent = (task.get("goal") or task.get("query") or "").lower()
        # contoh rule niat
        for dom in self.cfg.get("blocked_domains", []):
            if dom in intent:
                return "block", f"policy_block:{dom}"

        # rule komposisi: jika ada mass_outreach
        if steps:
            tools = [s.get("tool", "") for s in steps]
            if (
                tools.count("gmail.send") + tools.count("ms.mail.send") > 0
                and (task.get("recipients_gt", 0) or 0)
                > self.cfg["escalate_if"]["mass_outreach"]["recipients_gt"]
            ):
                return "escalate", "policy_escalate:mass_outreach"

        # rule transaksi finansial sederhana (placeholder)
        if (task.get("amount") or 0) > self.cfg["escalate_if"]["financial_tx"][
            "amount_gt"
        ]:
            return "escalate", "policy_escalate:financial_tx"
        intent = (task.get("goal") or task.get("query") or "").lower()
        if any(
            k in intent for k in ["distill_from_vendor", "finetune_with_vendor_output"]
        ):
            return "block", "policy_block:vendor_output_training"
        if (
            os.getenv("VENDOR_OUTPUT_TRAINING_BLOCK", "1") == "1"
            and task.get("source") == "vendor_api"
        ):
            return "block", "policy_block:vendor_output_source"

        return "ok", "policy_ok"
