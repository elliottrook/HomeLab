"""Strict readers for externally produced Forgejo and NetBox reports."""

from __future__ import annotations

import json
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MAX_REPORT_BYTES = 131_072
MAX_ITEMS = 256
MAX_AGE_SECONDS = 900
MAX_FUTURE_SECONDS = 60
SAFE_TEXT = re.compile(r"^[^\x00-\x1f\x7f]{1,200}$")
SAFE_STATUS = re.compile(r"^[a-z0-9_-]{1,40}$")
SHORT_SHA = re.compile(r"^[0-9a-f]{12}$")

FORGEJO_FIELDS = {
    "schema_version",
    "source",
    "generated_at",
    "instance",
    "repositories",
}
FORGEJO_REPOSITORY_FIELDS = {
    "owner",
    "name",
    "visibility",
    "archived",
    "default_branch",
    "updated_at",
    "counts",
    "latest_commit",
    "latest_action",
}
FORGEJO_COUNT_FIELDS = {
    "branches",
    "tags",
    "releases",
    "open_issues",
    "open_pulls",
}
FORGEJO_COMMIT_FIELDS = {"sha", "committed_at"}
FORGEJO_ACTION_FIELDS = {"status", "conclusion", "started_at"}

NETBOX_FIELDS = {
    "schema_version",
    "source",
    "generated_at",
    "instance",
    "inventory",
}
NETBOX_INVENTORY_FIELDS = {
    "counts",
    "devices",
    "virtual_machines",
    "vlans",
    "prefixes",
}
NETBOX_COUNT_FIELDS = {"devices", "virtual_machines", "sites", "racks", "vlans", "prefixes"}
DEVICE_FIELDS = {
    "name",
    "status",
    "role",
    "type",
    "site",
    "location",
    "rack",
    "position",
    "primary_ip4",
}
VM_FIELDS = {"name", "status", "role", "cluster", "site", "primary_ip4"}
VLAN_FIELDS = {"vid", "name", "status", "site"}
PREFIX_FIELDS = {"prefix", "status", "vlan", "site"}


def _unavailable(source: str, reason: str) -> dict[str, str]:
    return {"status": "unavailable", "source": source, "error": reason}


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else None


def _text(value: object, *, nullable: bool = False) -> bool:
    return (nullable and value is None) or (
        isinstance(value, str) and bool(SAFE_TEXT.fullmatch(value))
    )


def _count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 1_000_000


def _exact_dict(value: object, fields: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields


def _fresh(report: dict[str, Any], now: datetime | None) -> bool:
    generated = _timestamp(report.get("generated_at"))
    current = now or datetime.now(timezone.utc)
    if generated is None:
        return False
    age = (current - generated).total_seconds()
    return -MAX_FUTURE_SECONDS <= age <= MAX_AGE_SECONDS


def _validate_instance(value: object) -> bool:
    return _exact_dict(value, {"version"}) and _text(value["version"])


def _validate_forgejo(report: dict[str, Any]) -> bool:
    if (
        not _exact_dict(report, FORGEJO_FIELDS)
        or report.get("schema_version") != SCHEMA_VERSION
        or report.get("source") != "forgejo"
        or not _validate_instance(report.get("instance"))
    ):
        return False
    repositories = report.get("repositories")
    if not isinstance(repositories, list) or not 1 <= len(repositories) <= 16:
        return False
    for repository in repositories:
        if not _exact_dict(repository, FORGEJO_REPOSITORY_FIELDS):
            return False
        if (
            not _text(repository["owner"])
            or not _text(repository["name"])
            or repository["visibility"] not in {"private", "internal", "public"}
            or not isinstance(repository["archived"], bool)
            or not _text(repository["default_branch"])
            or _timestamp(repository["updated_at"]) is None
            or not _exact_dict(repository["counts"], FORGEJO_COUNT_FIELDS)
            or not all(_count(value) for value in repository["counts"].values())
        ):
            return False
        commit = repository["latest_commit"]
        if commit is not None and (
            not _exact_dict(commit, FORGEJO_COMMIT_FIELDS)
            or not isinstance(commit["sha"], str)
            or not SHORT_SHA.fullmatch(commit["sha"])
            or _timestamp(commit["committed_at"]) is None
        ):
            return False
        action = repository["latest_action"]
        if action is not None and (
            not _exact_dict(action, FORGEJO_ACTION_FIELDS)
            or not isinstance(action["status"], str)
            or not SAFE_STATUS.fullmatch(action["status"])
            or not (
                action["conclusion"] is None
                or (
                    isinstance(action["conclusion"], str)
                    and SAFE_STATUS.fullmatch(action["conclusion"])
                )
            )
            or _timestamp(action["started_at"]) is None
        ):
            return False
    return True


def _validate_netbox_item(
    item: object, fields: set[str], numeric: frozenset[str] = frozenset()
) -> bool:
    if not _exact_dict(item, fields):
        return False
    for name, value in item.items():
        if name in numeric:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 4094:
                return False
        elif not _text(value, nullable=True):
            return False
    return True


def _validate_netbox(report: dict[str, Any]) -> bool:
    if (
        not _exact_dict(report, NETBOX_FIELDS)
        or report.get("schema_version") != SCHEMA_VERSION
        or report.get("source") != "netbox"
        or not _validate_instance(report.get("instance"))
        or not _exact_dict(report.get("inventory"), NETBOX_INVENTORY_FIELDS)
    ):
        return False
    inventory = report["inventory"]
    counts = inventory["counts"]
    if not _exact_dict(counts, NETBOX_COUNT_FIELDS) or not all(_count(value) for value in counts.values()):
        return False
    specifications = (
        ("devices", DEVICE_FIELDS, frozenset()),
        ("virtual_machines", VM_FIELDS, frozenset()),
        ("vlans", VLAN_FIELDS, frozenset({"vid"})),
        ("prefixes", PREFIX_FIELDS, frozenset()),
    )
    for name, fields, numeric in specifications:
        items = inventory[name]
        if not isinstance(items, list) or len(items) > MAX_ITEMS:
            return False
        if not all(_validate_netbox_item(item, fields, numeric) for item in items):
            return False
    return True


def read_source_report(
    source: str,
    report_path: Path,
    *,
    now: datetime | None = None,
    required_uid: int | None = 0,
) -> dict[str, Any]:
    """Read one fresh report and return only its validated schema."""
    if source not in {"forgejo", "netbox"}:
        return _unavailable(source, "Unsupported report source")
    try:
        file_status = report_path.lstat()
        if not stat.S_ISREG(file_status.st_mode):
            raise ValueError("report is not a regular file")
        if required_uid is not None and file_status.st_uid != required_uid:
            raise ValueError("report has an untrusted owner")
        if file_status.st_mode & 0o022:
            raise ValueError("report is writable by group or other")
        if file_status.st_size > MAX_REPORT_BYTES:
            raise ValueError("report exceeds the maximum permitted size")
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _unavailable(source, f"Sanitized {source} report unavailable: {exc}")

    validator = _validate_forgejo if source == "forgejo" else _validate_netbox
    if not isinstance(report, dict) or not validator(report):
        return _unavailable(source, f"Sanitized {source} report has an invalid schema")
    if not _fresh(report, now):
        return _unavailable(source, f"Sanitized {source} report is stale or has an invalid timestamp")
    return report


def get_forgejo_report(report_path: Path, **kwargs: Any) -> dict[str, Any]:
    return read_source_report("forgejo", report_path, **kwargs)


def get_netbox_report(report_path: Path, **kwargs: Any) -> dict[str, Any]:
    return read_source_report("netbox", report_path, **kwargs)
