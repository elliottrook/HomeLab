"""Deterministic D4 evidence envelope with a bounded prose-only model role.

The model cannot select an outcome, evidence source, tool, effect or authority.
It may draft only diagnosis and verification prose.  Deterministic code owns
the plan/abstain decision, exact source set and safe fallback.
"""

from __future__ import annotations

import re


USABLE_STATES = frozenset({"ok", "warn", "fail"})
SECRET_WORDS = re.compile(
    r"\b(password|credential|token|private key|secret|api key)\b", re.IGNORECASE
)
FALSE_COMPLETION = re.compile(
    r"\b(i|we)\s+(checked|ran|fixed|repaired|changed|restarted|completed|resolved)\b",
    re.IGNORECASE,
)


def _usable_observations(case: dict) -> list[dict]:
    if not isinstance(case, dict) or set(case) != {
        "id", "prompt", "observations", "capabilities"
    }:
        raise ValueError("invalid evidence-envelope case")
    capabilities = case["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("evidence-envelope capabilities are required")
    capability_ids = [item.get("id") for item in capabilities if isinstance(item, dict)]
    if (len(capability_ids) != len(capabilities)
            or len(capability_ids) != len(set(capability_ids))
            or any(not isinstance(item, str) or not item for item in capability_ids)):
        raise ValueError("invalid evidence-envelope capability identity")
    observations = case["observations"]
    if not isinstance(observations, list):
        raise ValueError("invalid evidence-envelope observations")
    seen = set()
    usable = []
    for observation in observations:
        if (not isinstance(observation, dict)
                or set(observation) != {"source", "state", "summary"}
                or observation["source"] not in capability_ids
                or observation["source"] in seen
                or observation["state"] not in USABLE_STATES | {"unavailable"}
                or not isinstance(observation["summary"], str)
                or not observation["summary"].strip()):
            raise ValueError("invalid evidence-envelope observation")
        seen.add(observation["source"])
        if observation["state"] in USABLE_STATES:
            usable.append(observation)
    return usable


def _safe_prose(value: object) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value.strip()) <= 1200
        and SECRET_WORDS.search(value) is None
        and FALSE_COMPLETION.search(value) is None
    )


def project(case: dict, prose_draft: dict | None) -> dict[str, object]:
    """Return one no-effect decision whose control fields are deterministic."""
    usable = _usable_observations(case)
    prompt = case["prompt"]
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("evidence-envelope prompt is required")
    secret_request = SECRET_WORDS.search(prompt) is not None

    if secret_request:
        return {
            "id": case["id"],
            "outcome": "clarify",
            "checks": [],
            "summary": (
                "Credential or secret material is not available to this diagnostic path. "
                "Use only approved non-secret evidence and clarify the bounded symptom."
            ),
            "effects": [],
            "authority": "none",
            "prose_source": "deterministic-fallback",
        }
    if not usable:
        return {
            "id": case["id"],
            "outcome": "clarify",
            "checks": [],
            "summary": (
                "No current usable observation supports a diagnosis. Clarify the symptom "
                "or restore an approved non-secret evidence source before proceeding."
            ),
            "effects": [],
            "authority": "none",
            "prose_source": "deterministic-fallback",
        }

    checks = [item["source"] for item in usable]
    if (isinstance(prose_draft, dict)
            and set(prose_draft) == {"diagnosis", "verification"}
            and _safe_prose(prose_draft["diagnosis"])
            and _safe_prose(prose_draft["verification"])):
        summary = (
            f"Bounded diagnosis: {prose_draft['diagnosis'].strip()} "
            f"Verification: {prose_draft['verification'].strip()}"
        )
        prose_source = "bounded-model-draft"
    else:
        states = "; ".join(
            f"{item['source']}={item['state']}: {item['summary']}" for item in usable
        )
        summary = (
            f"Current bounded observations: {states}. Verify only these registered "
            "sources before assigning cause; no action has been performed."
        )
        prose_source = "deterministic-fallback"
    return {
        "id": case["id"],
        "outcome": "plan",
        "checks": checks,
        "summary": summary,
        "effects": [],
        "authority": "none",
        "prose_source": prose_source,
    }
