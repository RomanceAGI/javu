from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional
import os
import re, json, time


@dataclass
class ToolContract:
    name: str
    inputs_schema: Dict[str, Any] = field(
        default_factory=dict
    )  # pydantic-like (optional)
    outputs_schema: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[Callable[[Dict[str, Any]], bool]] = field(default_factory=list)
    postconditions: List[Callable[[Dict[str, Any]], bool]] = field(default_factory=list)
    side_effects: List[str] = field(
        default_factory=list
    )  # ["file.write","net.egress","gpu"]
    max_runtime_ms: int = 60_000
    max_output_bytes: int = 2_000_000
    allow_hosts: List[str] = field(default_factory=list)
    deny_hosts: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            k: getattr(self, k)
            for k in (
                "name",
                "inputs_schema",
                "outputs_schema",
                "side_effects",
                "max_runtime_ms",
                "max_output_bytes",
                "allow_hosts",
                "deny_hosts",
            )
        }


class ContractRegistry:
    def __init__(self):
        self._c: Dict[str, ToolContract] = {}

    def register(self, c: ToolContract):
        self._c[c.name] = c

    def get(self, name: str) -> Optional[ToolContract]:
        return self._c.get(name)

    def all(self):
        return list(self._c.values())


# helpers
def safe_filename(s: str) -> bool:
    return isinstance(s, str) and bool(re.match(r"^[\w.\-\/]{1,260}$", s))


def default_contracts() -> ContractRegistry:
    r = ContractRegistry()
    r.register(
        ToolContract(
            name="bash",
            side_effects=["file.write", "net.egress"],
            max_runtime_ms=30_000,
            max_output_bytes=500_000,
            deny_hosts=["169.254.169.254", "metadata.google.internal"],
        )
    )
    # Web
    r.register(
        ToolContract(
            name="web.get",
            inputs_schema={"url": {"type": "string"}, "timeout_s": {"type": "integer"}},
            preconditions=[
                lambda a: a.get("url", "").startswith(("http://", "https://"))
            ],
            postconditions=[
                lambda res: res.get("status") in {"ok", "blocked", "error"}
            ],
            side_effects=["net.egress"],
            max_runtime_ms=10000,
            allow_hosts=[h for h in os.getenv("EGRESS_ALLOWLIST", "").split(",") if h],
        )
    )
    r.register(
        ToolContract(
            name="web.head",
            inputs_schema={"url": {"type": "string"}, "timeout_s": {"type": "integer"}},
            preconditions=[
                lambda a: a.get("url", "").startswith(("http://", "https://"))
            ],
            postconditions=[
                lambda res: res.get("status") in {"ok", "blocked", "error"}
            ],
            side_effects=["net.egress"],
            max_runtime_ms=10000,
            allow_hosts=[h for h in os.getenv("EGRESS_ALLOWLIST", "").split(",") if h],
        )
    )

    # Storage
    r.register(
        ToolContract(
            name="storage.put_text",
            inputs_schema={"key": {"type": "string"}, "text": {"type": "string"}},
            preconditions=[lambda a: len(a.get("text", "")) <= 1_000_000],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["file.write", "net.egress"],
            max_runtime_ms=8000,
        )
    )
    r.register(
        ToolContract(
            name="storage.get_text",
            inputs_schema={"key": {"type": "string"}},
            preconditions=[lambda a: len(a.get("key", "")) <= 512],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["file.read", "net.egress"],
            max_runtime_ms=6000,
        )
    )

    # Telegram / Discord / Slack
    r.register(
        ToolContract(
            "slack.post_message",
            preconditions=[lambda a: len(a.get("text", "")) <= 4000],
            side_effects=["net.egress"],
        )
    )
    r.register(ToolContract("slack.list_messages"))
    r.register(
        ToolContract(
            "discord.post",
            preconditions=[lambda a: len(a.get("content", "")) <= 2000],
            side_effects=["net.egress"],
        )
    )
    r.register(ToolContract("discord.fetch"))
    r.register(
        ToolContract(
            "telegram.send",
            preconditions=[lambda a: len(a.get("text", "")) <= 4096],
            side_effects=["net.egress"],
        )
    )
    r.register(ToolContract("telegram.get_updates"))

    # GitHub
    r.register(
        ToolContract(
            name="github.create_issue",
            inputs_schema={"title": {"type": "string"}, "body": {"type": "string"}},
            preconditions=[lambda a: 1 <= len(a.get("title", "")) <= 200],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=8000,
        )
    )

    # Gmail
    r.register(
        ToolContract(
            "gmail.list_messages", preconditions=[lambda a: (a.get("max_n", 20) <= 100)]
        )
    )
    r.register(ToolContract("gmail.get_message"))
    r.register(
        ToolContract(
            "gmail.send",
            inputs_schema={
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            preconditions=[lambda a: len(a.get("body", "")) <= 20000],
            side_effects=["net.egress"],
        )
    )

    # GCal
    r.register(
        ToolContract(
            name="gcal.list_events",
            inputs_schema={
                "calendar_id": {"type": "string"},
                "q": {"type": "string"},
                "max_n": {"type": "integer"},
            },
            preconditions=[lambda a: len(a.get("q", "")) <= 256],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=8000,
        )
    )
    r.register(
        ToolContract(
            name="gcal.create_event",
            inputs_schema={
                "calendar_id": {"type": "string"},
                "title": {"type": "string"},
                "start_iso": {"type": "string"},
                "end_iso": {"type": "string"},
            },
            preconditions=[lambda a: len(a.get("title", "")) <= 200],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=8000,
        )
    )

    # GDrive / GContacts
    r.register(ToolContract("gdrive.list_files"))
    r.register(
        ToolContract(
            name="gdrive.download_file",
            inputs_schema={"file_id": {"type": "string"}},
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=30000,
            max_output_bytes=50_000_000,
        )
    )
    r.register(
        ToolContract(
            name="gdrive.upload_text",
            inputs_schema={
                "filename": {"type": "string"},
                "content": {"type": "string"},
            },
            side_effects=["net.egress"],
            max_runtime_ms=10000,
        )
    )

    r.register(ToolContract("gcontacts.list"))

    # MS Graph - Mail/Calendar/Files/Teams
    r.register(ToolContract("ms.mail.list_messages"))
    r.register(
        ToolContract(
            "ms.mail.send",
            preconditions=[lambda a: len(a.get("body", "")) <= 20000],
            side_effects=["net.egress"],
        )
    )
    r.register(ToolContract("ms.calendar.list_events"))
    r.register(
        ToolContract(
            "ms.calendar.create_event",
            preconditions=[lambda a: len(a.get("title", "")) <= 200],
            side_effects=["net.egress"],
        )
    )
    r.register(ToolContract("ms.files.list_root"))
    r.register(
        ToolContract(
            name="ms.files.download",
            inputs_schema={"item_id": {"type": "string"}},
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=30000,
            max_output_bytes=50_000_000,
        )
    )
    r.register(
        ToolContract(
            name="ms.files.upload_text",
            inputs_schema={
                "item_id": {"type": "string"},
                "content": {"type": "string"},
            },
            side_effects=["net.egress"],
            max_runtime_ms=10000,
        )
    )
    r.register(
        ToolContract(
            "ms.teams.post_message",
            preconditions=[lambda a: len(a.get("text", "")) <= 4000],
            side_effects=["net.egress"],
        )
    )
    r.register(ToolContract("ms.teams.list_messages"))

    # Notion
    r.register(
        ToolContract(
            name="notion.search",
            inputs_schema={
                "query": {"type": "string"},
                "page_size": {"type": "integer"},
            },
            preconditions=[
                lambda a: len(a.get("query", "")) <= 1024
                and int(a.get("page_size", 20)) <= 100
            ],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=10000,
            allow_hosts=["api.notion.com"],
        )
    )
    r.register(
        ToolContract(
            name="notion.create_page",
            inputs_schema={
                "parent_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
            },
            preconditions=[
                lambda a: len(a.get("title", "")) <= 200
                and len(a.get("content", "")) <= 20000
            ],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=12000,
            allow_hosts=["api.notion.com"],
        )
    )

    # Canva Proxy
    r.register(
        ToolContract(
            name="canva.create_design",
            inputs_schema={"name": {"type": "string"}, "brief": {"type": "string"}},
            preconditions=[
                lambda a: len(a.get("name", "")) <= 200
                and len(a.get("brief", "")) <= 20000
            ],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=15000,
        )
    )
    r.register(
        ToolContract(
            name="canva.publish",
            inputs_schema={
                "design_id": {"type": "string"},
                "destination": {"type": "string"},
            },
            preconditions=[lambda a: len(a.get("design_id", "")) <= 128],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=20000,
        )
    )
    r.register(
        ToolContract(
            name="canva.list_designs",
            inputs_schema={"q": {"type": "string"}, "limit": {"type": "integer"}},
            preconditions=[
                lambda a: int(a.get("limit", 20)) <= 100 and len(a.get("q", "")) <= 1024
            ],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=10000,
        )
    )

    # MS Graph Files (SharePoint site)
    r.register(
        ToolContract(
            name="ms.files.list_site_drive",
            inputs_schema={"site_id": {"type": "string"}, "top": {"type": "integer"}},
            preconditions=[lambda a: int(a.get("top", 50)) <= 200],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["net.egress"],
            max_runtime_ms=12000,
            allow_hosts=["graph.microsoft.com"],
        )
    )

    # Agriculture
    r.register(
        ToolContract(
            name="apply_fertilizer",
            inputs_schema={
                "field_id": {"type": "string"},
                "n_kg": {"type": "number"},
                "p_kg": {"type": "number"},
                "k_kg": {"type": "number"},
                "method": {"type": "string"},
            },
            preconditions=[
                lambda a: float(a.get("n_kg", 0)) <= 50
                and float(a.get("p_kg", 0)) <= 30
                and float(a.get("k_kg", 0)) <= 30
            ],
            side_effects=["planet.agriculture"],
            max_runtime_ms=8000,
        )
    )
    r.register(
        ToolContract(
            name="irrigate",
            inputs_schema={
                "field_id": {"type": "string"},
                "m3": {"type": "number"},
                "time_window": {"type": "string"},
            },
            preconditions=[lambda a: float(a.get("m3", 0)) <= 50],
            side_effects=["planet.agriculture"],
            max_runtime_ms=8000,
        )
    )
    # Oil & Gas
    r.register(
        ToolContract(
            name="drill_execute",
            inputs_schema={
                "pad_id": {"type": "string"},
                "depth_m": {"type": "number"},
                "mud_plan_id": {"type": "string"},
            },
            preconditions=[lambda a: float(a.get("depth_m", 0)) <= 3500],
            postconditions=[],
            side_effects=["planet.oil_gas", "physical"],
            max_runtime_ms=20000,
        )
    )
    r.register(
        ToolContract(
            name="pipeline_route",
            inputs_schema={
                "geojson": {"type": "string"},
                "buffer_m": {"type": "number"},
            },
            side_effects=["planet.oil_gas"],
            max_runtime_ms=12000,
        )
    )
    # Infrastructure
    r.register(
        ToolContract(
            name="pour_concrete",
            inputs_schema={
                "site_id": {"type": "string"},
                "m3": {"type": "number"},
                "mix_type": {"type": "string"},
            },
            preconditions=[lambda a: float(a.get("m3", 0)) <= 200],
            side_effects=["planet.infrastructure", "physical"],
            max_runtime_ms=15000,
        )
    )
    r.register(
        ToolContract(
            name="route_plan",
            inputs_schema={
                "geojson": {"type": "string"},
                "objectives": {"type": "array"},
            },
            side_effects=["planet.infrastructure"],
            max_runtime_ms=12000,
        )
    )
    return r


_orig_default_contracts = default_contracts


@dataclass
class PiiPolicy:
    allow: bool = False
    redact_rules: Dict[str, str] = field(
        default_factory=lambda: {
            r"\b\d{16}\b": "[REDACT_CARD]",
            r"\b\d{3}-\d{3,4}-\d{4}\b": "[REDACT_PHONE]",
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}": "[REDACT_EMAIL]",
        }
    )


@dataclass
class RegionPolicy:
    regions_allowed: List[str] = field(default_factory=list)
    regions_denied: List[str] = field(default_factory=list)


@dataclass
class ApprovalPolicy:
    require_human_approval: bool = False
    reason: str = ""


def _compose_contracts() -> ContractRegistry:
    r = _orig_default_contracts()

    # 1) Hard-OFF training/finetune/distill/dataset-export
    for _n in [
        "llm.autotrain.start",
        "llm.finetune.start",
        "llm.distill.start",
        "dataset.export_for_training",
    ]:
        r.register(
            ToolContract(name=_n, preconditions=[lambda a: False], side_effects=[])
        )

    # 2) Governance primitives always allowed (no side-effects)
    for _n in [
        "eco_guard.enforce",
        "transparency.report",
        "ethical_critic.precheck",
        "ethical_critic.postcheck",
        "introspection.explain",
        "audit.write",
        "resilience.observe",
        "coach.refine",
    ]:
        r.register(
            ToolContract(name=_n, preconditions=[lambda a: True], side_effects=[])
        )

    # 3) Add high-risk tools with stricter preconditions
    r.register(
        ToolContract(
            name="file.write",
            inputs_schema={"path": {"type": "string"}, "text": {"type": "string"}},
            preconditions=[
                lambda a: safe_filename(a.get("path", ""))
                and len(a.get("text", "")) <= 2_000_000
            ],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["file.write"],
            max_runtime_ms=8000,
        )
    )
    r.register(
        ToolContract(
            name="code.exec",
            inputs_schema={"lang": {"type": "string"}, "code": {"type": "string"}},
            preconditions=[
                lambda a: a.get("lang") in {"python", "bash"}
                and len(a.get("code", "")) <= 100_000
            ],
            postconditions=[lambda res: res.get("status") in {"ok", "error"}],
            side_effects=["cpu", "file.write"],
            max_runtime_ms=30_000,
            max_output_bytes=2_000_000,
        )
    )

    return r


# Export: make composed registry the default
def default_contracts() -> ContractRegistry:
    return _compose_contracts()


# Global governance knobs
_PII = PiiPolicy(
    allow=(os.getenv("ALLOW_PII", "0") in {"1", "true", "TRUE"}),
)
_REGION = RegionPolicy(
    regions_allowed=[x for x in os.getenv("REGIONS_ALLOWED", "").split(",") if x],
    regions_denied=[x for x in os.getenv("REGIONS_DENIED", "").split(",") if x],
)
_APPROVAL = ApprovalPolicy(
    require_human_approval=(
        os.getenv("REQUIRE_APPROVAL", "0") in {"1", "true", "TRUE"}
    ),
    reason=os.getenv("APPROVAL_REASON", ""),
)


def _redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if _PII.allow:
        return payload
    s = json.dumps(payload, ensure_ascii=False)
    for pat, rep in _PII.redact_rules.items():
        s = re.sub(pat, rep, s)
    return json.loads(s)


def enforce_contract(
    registry: ContractRegistry,
    tool: str,
    args: Dict[str, Any],
    *,
    user_region: str = "",
) -> Dict[str, Any]:
    """
    Validasi + sanitasi sebelum eksekusi tool. Return {ok, reason, args_sanitized, approval_required}.
    """
    c = registry.get(tool)
    if not c:
        return {
            "ok": False,
            "reason": f"unknown tool '{tool}'",
            "args_sanitized": args,
            "approval_required": False,
        }

    # Region policy
    if user_region:
        if _REGION.regions_denied and user_region in _REGION.regions_denied:
            return {
                "ok": False,
                "reason": f"region '{user_region}' denied",
                "args_sanitized": args,
                "approval_required": False,
            }
        if _REGION.regions_allowed and user_region not in _REGION.regions_allowed:
            return {
                "ok": False,
                "reason": f"region '{user_region}' not allowed",
                "args_sanitized": args,
                "approval_required": False,
            }

    # Preconditions
    try:
        for p in c.preconditions or []:
            if not p(args):
                return {
                    "ok": False,
                    "reason": "precondition_failed",
                    "args_sanitized": args,
                    "approval_required": False,
                }
    except Exception as e:
        return {
            "ok": False,
            "reason": f"precheck_error:{e}",
            "args_sanitized": args,
            "approval_required": False,
        }

    # Redact PII
    args_sanitized = _redact_payload(args)

    # Approval
    approval_required = _APPROVAL.require_human_approval and (
        "physical" in (c.side_effects or [])
    )

    return {
        "ok": True,
        "reason": "ok",
        "args_sanitized": args_sanitized,
        "approval_required": approval_required,
    }
