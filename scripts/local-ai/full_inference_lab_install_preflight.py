"""No-effect target-Linux import and command-contract preflight."""

from __future__ import annotations

import importlib

from cooperative_lab_host_adapter import CooperativeHostObserver
from full_inference_lab_session import FULL_DRAIN_CONSUMERS, canonical_commands


REQUIRED_MODULES = (
    "application_b60_lease", "host_exclusion", "cooperative_lab_session",
    "cooperative_lab_host_adapter", "full_inference_lab_session",
    "full_inference_lab_sources", "full_inference_lab_validator",
    "full_inference_lab_runtime",
)


def validate_imports() -> dict[str, object]:
    """Import only pinned modules and validate fixed command shapes; no runner."""
    for name in REQUIRED_MODULES:
        importlib.import_module(name)
    drain, restore = canonical_commands()
    if len(drain) != 5 or len(FULL_DRAIN_CONSUMERS) != 5 or len(restore) != 11:
        raise ValueError("full-drain command inventory is incomplete")
    if any(command[:2] != ("pct", "exec") for command in (*drain, *restore)):
        raise ValueError("full-drain command boundary is invalid")
    return {"modules": len(REQUIRED_MODULES), "drain_effects": len(drain),
            "restore_effects": len(restore), "effects": "not-attempted"}
