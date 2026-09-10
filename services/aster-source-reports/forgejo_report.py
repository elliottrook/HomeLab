#!/usr/bin/env python3
"""Produce a fixed, content-free Forgejo metadata report for Aster."""

from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from source_reports import get_forgejo_report


ORIGIN = "http://127.0.0.1:3000"
REPOSITORIES = (("jason", "homelab"),)
TOKEN_PATH = Path(os.environ.get("ASTER_FORGEJO_TOKEN_FILE", "/etc/aster-forgejo-report/token"))
OUTPUT_PATH = Path(
    os.environ.get("ASTER_FORGEJO_REPORT_OUTPUT", "/var/lib/aster-forgejo-report/latest.json")
)
MAX_RESPONSE_BYTES = 1_048_576


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def _token() -> str:
    value = TOKEN_PATH.read_text(encoding="utf-8").strip()
    if not value or len(value) > 256 or any(character.isspace() for character in value):
        raise ValueError("invalid Forgejo report token")
    return value


def _get(path: str, token: str) -> tuple[Any, dict[str, str]]:
    if not path.startswith("/api/v1/"):
        raise ValueError("invalid Forgejo API path")
    request = urllib.request.Request(
        ORIGIN + path,
        headers={"Authorization": f"token {token}", "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=10) as response:
            if response.status != 200:
                raise ValueError("unexpected Forgejo response")
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("Forgejo response exceeded limit")
            return json.loads(body), {name.casefold(): value for name, value in response.headers.items()}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError("Forgejo metadata request failed") from exc


def _list(path: str, token: str) -> tuple[list[Any], int]:
    separator = "&" if "?" in path else "?"
    payload, headers = _get(f"{path}{separator}limit=50&page=1", token)
    if not isinstance(payload, list):
        raise ValueError("invalid Forgejo list response")
    total_value = headers.get("x-total-count")
    total = int(total_value) if total_value is not None else len(payload)
    if total < len(payload) or total > 1_000_000:
        raise ValueError("invalid Forgejo result count")
    return payload, total


def _timestamp(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("missing Forgejo timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("naive Forgejo timestamp")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _latest_action(payload: object) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list) or not runs:
        return None
    run = runs[0]
    if not isinstance(run, dict):
        return None
    started = run.get("run_started_at") or run.get("started_at") or run.get("created_at")
    status = run.get("status")
    conclusion = run.get("conclusion")
    if not isinstance(status, str):
        return None
    return {
        "status": status.casefold().replace(" ", "_")[:40],
        "conclusion": (
            conclusion.casefold().replace(" ", "_")[:40]
            if isinstance(conclusion, str) and conclusion
            else None
        ),
        "started_at": _timestamp(started),
    }


def build_report(now: datetime | None = None) -> dict[str, Any]:
    token = _token()
    version, _headers = _get("/api/v1/version", token)
    if not isinstance(version, dict) or not isinstance(version.get("version"), str):
        raise ValueError("invalid Forgejo version response")
    repositories = []
    for owner, name in REPOSITORIES:
        quoted_owner = urllib.parse.quote(owner, safe="")
        quoted_name = urllib.parse.quote(name, safe="")
        base = f"/api/v1/repos/{quoted_owner}/{quoted_name}"
        repository, _headers = _get(base, token)
        if not isinstance(repository, dict):
            raise ValueError("invalid Forgejo repository response")
        _branches, branch_count = _list(f"{base}/branches", token)
        _tags, tag_count = _list(f"{base}/tags", token)
        _releases, release_count = _list(f"{base}/releases", token)
        _issues, issue_count = _list(f"{base}/issues?state=open&type=issues", token)
        _pulls, pull_count = _list(f"{base}/pulls?state=open", token)
        commits, _commit_count = _list(f"{base}/commits", token)
        action_payload, _headers = _get(f"{base}/actions/runs?limit=1&page=1", token)
        latest_commit = None
        if commits:
            commit = commits[0]
            committed_at = (
                commit.get("commit", {}).get("committer", {}).get("date")
                if isinstance(commit, dict)
                else None
            )
            sha = commit.get("sha") if isinstance(commit, dict) else None
            if not isinstance(sha, str) or len(sha) < 12:
                raise ValueError("invalid Forgejo commit response")
            latest_commit = {"sha": sha[:12].casefold(), "committed_at": _timestamp(committed_at)}
        visibility = "private" if repository.get("private") else (
            "internal" if repository.get("internal") else "public"
        )
        repositories.append(
            {
                "owner": owner,
                "name": name,
                "visibility": visibility,
                "archived": bool(repository.get("archived")),
                "default_branch": str(repository.get("default_branch") or "main")[:200],
                "updated_at": _timestamp(repository.get("updated_at")),
                "counts": {
                    "branches": branch_count,
                    "tags": tag_count,
                    "releases": release_count,
                    "open_issues": issue_count,
                    "open_pulls": pull_count,
                },
                "latest_commit": latest_commit,
                "latest_action": _latest_action(action_payload),
            }
        )
    generated = now or datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "source": "forgejo",
        "generated_at": generated.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "instance": {"version": version["version"][:200]},
        "repositories": repositories,
    }


def write_report(report: dict[str, Any], output: Path = OUTPUT_PATH) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, candidate_name = tempfile.mkstemp(prefix=".candidate-", dir=output.parent)
    candidate = Path(candidate_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(report, handle, separators=(",", ":"), sort_keys=True)
            handle.write("\n")
        candidate.chmod(0o600)
        validated = get_forgejo_report(candidate, required_uid=None)
        if validated.get("status") == "unavailable":
            raise ValueError(validated["error"])
        candidate.replace(output)
    finally:
        candidate.unlink(missing_ok=True)


def main() -> int:
    write_report(build_report())
    print("source=forgejo status=refreshed repositories=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
