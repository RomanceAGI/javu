from __future__ import annotations
from typing import Dict, Any, List


class ConflictMediator:
    def propose(
        self, parties: List[str], interests: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        # naive synthesis: intersection = agreement, remainder = negotiate with concessions
        agree = (
            set.intersection(*(set(interests.get(p, [])) for p in parties))
            if parties
            else set()
        )
        rest = {p: list(set(interests.get(p, [])) - agree) for p in parties}
        options = [
            {"type": "baseline", "terms": list(agree)},
            {
                "type": "concession_cycle",
                "terms": [f"{p} concedes minor on {rest[p][:1]}" for p in parties],
            },
            {
                "type": "time_bounded_trial",
                "terms": ["trial for 90 days", "joint review"],
            },
        ]
        mou = {
            "parties": parties,
            "principles": ["non-violence", "mutual benefit", "transparency"],
            "terms": options[0]["terms"],
            "review": "quarterly",
        }
        return {
            "agreement": list(agree),
            "open_items": rest,
            "options": options,
            "mou": mou,
        }
