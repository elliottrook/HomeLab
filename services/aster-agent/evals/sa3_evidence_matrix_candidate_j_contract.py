"""Candidate-j source contract: registered hypotheses, deterministic prose."""

from __future__ import annotations

from sa3_deterministic_evidence_envelope_v1 import SECRET_WORDS, _safe_prose


STATES = frozenset({"ok", "warn", "fail", "unavailable"})
FRESHNESS = frozenset({"current", "stale", "unknown"})


def _validate(case: object) -> tuple[dict, dict[str, dict], dict[str, dict]]:
    if not isinstance(case, dict) or set(case) != {
        "id", "prompt", "observations", "capabilities", "hypotheses"
    }:
        raise ValueError("candidate-j case schema is invalid")
    if (not isinstance(case["id"], str) or not case["id"]
            or not isinstance(case["prompt"], str) or not case["prompt"].strip()
            or not isinstance(case["observations"], list)
            or not isinstance(case["capabilities"], list)
            or not isinstance(case["hypotheses"], list)):
        raise ValueError("candidate-j case identity or collections are invalid")

    capabilities: dict[str, dict] = {}
    for row in case["capabilities"]:
        if (not isinstance(row, dict) or set(row) != {"id", "description"}
                or not isinstance(row["id"], str) or not row["id"]
                or row["id"] in capabilities
                or not isinstance(row["description"], str)
                or not row["description"].strip()):
            raise ValueError("candidate-j capability is invalid")
        capabilities[row["id"]] = row

    observations: dict[str, dict] = {}
    for row in case["observations"]:
        if (not isinstance(row, dict)
                or set(row) != {"source", "state", "summary", "freshness"}
                or row["source"] not in capabilities
                or row["source"] in observations
                or row["state"] not in STATES
                or row["freshness"] not in FRESHNESS
                or not isinstance(row["summary"], str)
                or not row["summary"].strip()
                or not _safe_prose(row["summary"])):
            raise ValueError("candidate-j observation is invalid")
        observations[row["source"]] = row

    hypotheses: dict[str, dict] = {}
    for row in case["hypotheses"]:
        if (not isinstance(row, dict) or set(row) != {
                "id", "claim", "supports", "contradicts", "checks"}
                or not isinstance(row["id"], str) or not row["id"]
                or row["id"] in hypotheses
                or not isinstance(row["claim"], str)
                or not _safe_prose(row["claim"])
                or any(not isinstance(value, list)
                       for value in (row["supports"], row["contradicts"],
                                     row["checks"]))
                or not row["supports"]
                or len(row["supports"]) != len(set(row["supports"]))
                or len(row["contradicts"]) != len(set(row["contradicts"]))
                or len(row["checks"]) != len(set(row["checks"]))
                or not set(row["supports"]) <= set(observations)
                or not set(row["contradicts"]) <= set(observations)
                or set(row["supports"]) & set(row["contradicts"])
                or not set(row["checks"]) <= set(capabilities)):
            raise ValueError("candidate-j hypothesis is invalid")
        hypotheses[row["id"]] = row
    if not capabilities or not hypotheses:
        raise ValueError("candidate-j requires registered evidence and hypotheses")
    return case, observations, hypotheses


def _checks(hypotheses: dict[str, dict]) -> list[str]:
    return sorted({check for row in hypotheses.values() for check in row["checks"]})


def _clarify(case: dict, hypotheses: dict[str, dict], reason: str) -> dict:
    return {
        "id": case["id"], "outcome": "clarify", "checks": _checks(hypotheses),
        "summary": (
            f"Bounded assessment: {reason} Verification: use only the listed "
            "registered read-only checks to obtain current non-secret evidence; "
            "no cause is assigned and no action has been performed."
        ),
        "effects": [], "authority": "none",
        "prose_source": "deterministic-evidence-matrix",
    }


def project(case: object, selection: object) -> dict[str, object]:
    """Render a bounded answer; a model may select IDs but author no prose."""
    case, observations, hypotheses = _validate(case)
    if SECRET_WORDS.search(case["prompt"]) is not None:
        return _clarify(case, hypotheses, "the request depends on secret material")

    current = {
        source: row for source, row in observations.items()
        if row["freshness"] == "current" and row["state"] != "unavailable"
    }
    if not current:
        return _clarify(case, hypotheses,
                        "no current usable observation supports a diagnosis")

    eligible = {
        name: row for name, row in hypotheses.items()
        if set(row["supports"]) <= set(current)
    }
    if (not isinstance(selection, dict) or set(selection) != {"hypothesis_ids"}
            or not isinstance(selection["hypothesis_ids"], list)
            or not 1 <= len(selection["hypothesis_ids"]) <= 2
            or len(selection["hypothesis_ids"])
            != len(set(selection["hypothesis_ids"]))
            or not set(selection["hypothesis_ids"]) <= set(eligible)):
        return _clarify(case, hypotheses,
                        "no registered evidence-supported hypothesis was selected")

    selected = [eligible[name] for name in selection["hypothesis_ids"]]
    evidence_sources = sorted({source for row in selected
                               for source in row["supports"]})
    checks = sorted({check for row in selected for check in row["checks"]})
    facts = "; ".join(
        f"{source} is {current[source]['state']}: {current[source]['summary']}"
        for source in evidence_sources
    )
    claims = "; ".join(f"possible: {row['claim']}" for row in selected)
    return {
        "id": case["id"], "outcome": "plan", "checks": checks,
        "summary": (
            f"Current bounded evidence: {facts}. Registered hypotheses: {claims}. "
            "These are hypotheses, not established causes. Verification: refresh "
            f"the registered checks {', '.join(checks)} and compare current states "
            "before assigning cause; no action has been performed."
        ),
        "effects": [], "authority": "none",
        "prose_source": "deterministic-evidence-matrix",
    }
