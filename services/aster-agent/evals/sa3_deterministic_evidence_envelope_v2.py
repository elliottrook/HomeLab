"""Candidate-i: deterministic verification with diagnosis-only model prose."""
from __future__ import annotations

from sa3_deterministic_evidence_envelope_v1 import (
    SECRET_WORDS, _safe_prose, _usable_observations,
)


def project(case: dict, diagnosis_draft: object) -> dict[str, object]:
    """Return a no-effect decision whose verification is never model-authored."""
    usable = _usable_observations(case)
    prompt = case.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("evidence-envelope prompt is required")
    if SECRET_WORDS.search(prompt) is not None:
        return {
            "id": case["id"], "outcome": "clarify", "checks": [],
            "summary": (
                "Bounded diagnosis: the request depends on secret material that this "
                "path cannot access. Verification: restate the bounded symptom and "
                "inspect only an approved current non-secret evidence source."
            ),
            "effects": [], "authority": "none",
            "prose_source": "deterministic-diagnosis",
        }
    if not usable:
        return {
            "id": case["id"], "outcome": "clarify", "checks": [],
            "summary": (
                "Bounded diagnosis: no current usable observation supports a cause. "
                "Verification: clarify the symptom and restore one approved current "
                "non-secret evidence source before reassessment."
            ),
            "effects": [], "authority": "none",
            "prose_source": "deterministic-diagnosis",
        }
    checks = [item["source"] for item in usable]
    if (isinstance(diagnosis_draft, dict)
            and set(diagnosis_draft) == {"diagnosis"}
            and _safe_prose(diagnosis_draft["diagnosis"])):
        diagnosis = diagnosis_draft["diagnosis"].strip()
        prose_source = "bounded-model-diagnosis"
    else:
        diagnosis = "; ".join(
            f"{item['source']}={item['state']}: {item['summary']}"
            for item in usable
        )
        prose_source = "deterministic-diagnosis"
    sources = ", ".join(checks)
    summary = (
        f"Bounded diagnosis: {diagnosis} Verification: refresh the registered "
        f"sources {sources} and confirm their current states and freshness before "
        "assigning cause; no action has been performed."
    )
    return {
        "id": case["id"], "outcome": "plan", "checks": checks,
        "summary": summary, "effects": [], "authority": "none",
        "prose_source": prose_source,
    }
