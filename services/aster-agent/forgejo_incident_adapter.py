"""Aggregate the fixed sanitized Forgejo report into one safe observation.

Repository names, owners, branches, commit identities and action timestamps are
never copied into incident evidence. The adapter reads no Git remote and has no
network, credential, subprocess or repair capability.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from source_reports import get_forgejo_report
from sysadmin_investigation import Observation


SOURCE = "forgejo-main-report/v1"
FAILURE_CONCLUSIONS = frozenset({
    "failure", "failed", "timed_out", "cancelled", "canceled",
    "startup_failure", "stale",
})


def _unavailable(incident_id: str, now: datetime) -> Observation:
    marker = hashlib.sha256((incident_id + "\0forgejo-unavailable").encode()).hexdigest()[:24]
    return Observation(
        evidence_id="forgejo-unavailable-" + marker,
        incident_id=incident_id,
        target="forgejo-main",
        kind="git",
        observed_at=now.isoformat().replace("+00:00", "Z"),
        source=SOURCE,
        state="unavailable",
        summary="Sanitized Forgejo status is unavailable.",
        facts={"reason": "source_unavailable"},
        truncated=False,
    )


def read_forgejo_observation(
    incident_id: str,
    report_path: Path,
    now: datetime,
    *,
    reader: Callable = get_forgejo_report,
) -> Observation:
    """Return aggregate health only from the existing fixed report."""
    report = reader(report_path, now=now)
    if not isinstance(report, dict) or report.get("status") == "unavailable":
        return _unavailable(incident_id, now)
    repositories = report["repositories"]
    failed_actions = 0
    pending_actions = 0
    archived = 0
    open_issues = 0
    open_pulls = 0
    for repository in repositories:
        archived += int(repository["archived"])
        open_issues += repository["counts"]["open_issues"]
        open_pulls += repository["counts"]["open_pulls"]
        action = repository["latest_action"]
        if action is None:
            continue
        conclusion = action["conclusion"]
        if conclusion in FAILURE_CONCLUSIONS:
            failed_actions += 1
        elif conclusion != "success":
            pending_actions += 1
    state = "fail" if failed_actions else "warn" if pending_actions else "ok"
    digest = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:24]
    return Observation(
        evidence_id="forgejo-" + digest,
        incident_id=incident_id,
        target="forgejo-main",
        kind="git",
        observed_at=report["generated_at"],
        source=SOURCE,
        state=state,
        summary=(
            f"Sanitized Forgejo status covers {len(repositories)} repositories; "
            f"{failed_actions} latest actions failed and {pending_actions} are nonterminal."
        ),
        facts={
            "repository_count": len(repositories),
            "archived_count": archived,
            "open_issue_count": open_issues,
            "open_pull_count": open_pulls,
            "failed_latest_action_count": failed_actions,
            "pending_latest_action_count": pending_actions,
            "report_digest": digest,
        },
        truncated=False,
    )
