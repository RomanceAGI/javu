from __future__ import annotations
import json, glob, os, random
from typing import List, Dict, Any
from javu_agi.mbrl import MBWorld
from javu_agi.state_space import StructuredState

def iter_episodes(dir_glob: str) -> List[Dict[str,Any]]:
    files = glob.glob(dir_glob, recursive=True)
    for fp in files:
        try:
            with open(fp,"r",encoding="utf-8") as f: yield json.load(f)
        except Exception: continue

# === ToS Guard: disable vendor-output distillation / MBWorld fitting ===
try:
    from javu_agi.registry import guard_training_call, PolicyViolationError
except Exception:
    class PolicyViolationError(RuntimeError): ...
    def guard_training_call(action: str, **kw):
        raise PolicyViolationError("Training/distillation blocked by policy")

def fit_mb_from_distill(
    data_dir: str = "/data/metrics",
    skills_dir: str = "/data/skills",
    k: int = 5000,
    *,
    dataset_meta: dict | None = None,
    context: dict | None = None,
) -> None:
    """
    Disabled function for fitting a model-based world from distilled vendor outputs.

    Using vendor model outputs as training signals is disallowed by the vendor's
    terms of service.  This stub performs a policy check via ``guard_training_call``
    and then raises ``PolicyViolationError`` unconditionally.

    Parameters
    ----------
    data_dir : str, optional
        Directory of metrics (unused).
    skills_dir : str, optional
        Directory of skills (unused).
    k : int, optional
        Number of samples to consider (unused).
    dataset_meta : dict, optional
        Metadata describing the dataset.  If omitted, it is assumed to contain vendor outputs.
    context : dict, optional
        Additional context for the policy guard.  Defaults to specifying an unknown source vendor.

    Raises
    ------
    PolicyViolationError
        Always raised to enforce the vendor policy prohibiting training on vendor outputs.
    """
    guard_training_call(
        "distill",
        dataset_meta=dataset_meta or {"contains_vendor_outputs": True},
        context=context or {"source_vendor": "unknown"},
    )
    # Regardless of guard outcome, enforce the policy by raising.
    raise PolicyViolationError(
        "fit_mb_from_distill is disabled by policy (no vendor-output distillation)."
    )
