"""Compiled SA4 target registry with one owner-approved inert canary.

Runtime callers can name only a target ID.  They cannot supply a registry,
path, host, postcheck, rollback implementation, or review identity.  The
synthetic fixture remains available only to source/schema tests.  The sole
production registration names an absent, inert target and grants no authority
to create, install, measure or repair it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import PurePosixPath
import re


HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
FORBIDDEN_PREFIXES = (
    "/boot", "/dev", "/etc/crypttab", "/etc/fstab", "/etc/group",
    "/etc/gshadow", "/etc/hosts", "/etc/network", "/etc/passwd",
    "/etc/shadow", "/etc/ssh", "/proc", "/root", "/run/secrets",
    "/sys", "/var/lib/openbao",
)


@dataclass(frozen=True)
class Target:
    target_id: str
    host_id: str
    path: str
    owner: str
    group: str
    mode: str
    classification: str
    checkpoint_parent: str
    temporary_path: str
    maximum_bytes: int
    postcheck_ids: tuple[str, ...]
    postcheck_program_sha256: tuple[str, ...]
    rollback_program_sha256: str
    owner_review_sha256: str
    regular_file: bool = True
    follow_symlinks: bool = False
    one_link: bool = True
    service_restart_required: bool = False
    automatic_retry: bool = False


SCHEMA_FIXTURES = (
    Target(
        target_id="sa4-synthetic-fixture",
        host_id="synthetic-host",
        path="/synthetic/aster/example.conf",
        owner="root", group="root", mode="0644",
        classification="low-criticality-read-only-adapter",
        checkpoint_parent="/synthetic/checkpoints",
        temporary_path="/synthetic/aster/.example.conf.sa4-tmp",
        maximum_bytes=4096,
        postcheck_ids=("target-bytes", "target-metadata",
                       "consumer-read-only-health"),
        postcheck_program_sha256=("1" * 64, "2" * 64, "3" * 64),
        rollback_program_sha256="4" * 64,
        owner_review_sha256="5" * 64,
    ),
)

# Owner acceptance is retained as
# SA4-first-target-owner-acceptance-2026-11-05.json. The path is absent until a
# later exact inactive-install packet; source registration is not deployment.
PRODUCTION_TARGETS: tuple[Target, ...] = (
    Target(
        target_id="sa4-lxc104-canary-adapter-v1",
        host_id="lxc104",
        path="/var/lib/aster/sa4/canary-adapter.json",
        owner="root", group="root", mode="0644",
        classification="low-criticality-read-only-adapter",
        checkpoint_parent="/var/lib/aster/sa4/checkpoints",
        temporary_path="/var/lib/aster/sa4/.canary-adapter.json.sa4-tmp",
        maximum_bytes=4096,
        postcheck_ids=("target-bytes", "target-metadata",
                       "consumer-read-only-health"),
        postcheck_program_sha256=(
            "f8f544ca04b7587b76d827ea1e193c56bb814a231b498c6652009e098bdd00a1",
            "e61bb89bd366e03fed0bafaa23b18db484f1b2a6133b2a708469b9b66d49a041",
            "1214189f36c4bb75a90028cd31c15f4dd5ecf6977582ada67cd72a5ce65c72da"),
        rollback_program_sha256=
        "15f924f589980d786e7d0f8ad5ac5f03e32e95d907737a6c2d4ae9adad61ffdb",
        owner_review_sha256=
        "5a47af308226e66ce7c1d5b5c6450d3c846ee175152448a85be5e766b663fe3d",
    ),
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _path(value: str) -> bool:
    return (value.startswith("/") and "\x00" not in value
            and value == str(PurePosixPath(value))
            and ".." not in PurePosixPath(value).parts)


def _digest(value: str) -> bool:
    return bool(HEX64.fullmatch(value))


def validate_registry(entries: tuple[Target, ...], *, synthetic: bool) -> None:
    if not isinstance(entries, tuple) or any(not isinstance(item, Target)
                                              for item in entries):
        raise ValueError("SA4 registry must be a compiled target tuple")
    identities: set[str] = set()
    locations: set[tuple[str, str]] = set()
    for item in entries:
        location = (item.host_id, item.path)
        paths = (item.path, item.checkpoint_parent, item.temporary_path)
        if (not IDENTITY.fullmatch(item.target_id)
                or not IDENTITY.fullmatch(item.host_id)
                or not IDENTITY.fullmatch(item.owner)
                or not IDENTITY.fullmatch(item.group)
                or item.target_id in identities or location in locations
                or any(not _path(path) for path in paths)
                or len(set(paths)) != 3
                or item.path.startswith(item.checkpoint_parent + "/")
                or item.temporary_path.startswith(item.checkpoint_parent + "/")
                or item.mode != "0644" or item.owner != "root"
                or item.group != "root" or item.regular_file is not True
                or item.follow_symlinks is not False or item.one_link is not True
                or item.service_restart_required is not False
                or item.automatic_retry is not False
                or item.classification != "low-criticality-read-only-adapter"
                or type(item.maximum_bytes) is not int
                or not 1 <= item.maximum_bytes <= 1_048_576
                or item.postcheck_ids != (
                    "target-bytes", "target-metadata",
                    "consumer-read-only-health")
                or len(item.postcheck_program_sha256) != 3
                or any(not _digest(value)
                       for value in item.postcheck_program_sha256)
                or not _digest(item.rollback_program_sha256)
                or not _digest(item.owner_review_sha256)
                or (not synthetic and any(item.path == prefix
                    or item.path.startswith(prefix + "/")
                    for prefix in FORBIDDEN_PREFIXES))):
            raise ValueError("SA4 compiled target registration is unsafe")
        identities.add(item.target_id)
        locations.add(location)


def registration_document(item: Target) -> dict[str, object]:
    value = asdict(item)
    value["schema"] = "aster-sa4-target-registration.v1"
    value["postcheck_ids"] = list(item.postcheck_ids)
    value["postcheck_program_sha256"] = list(
        item.postcheck_program_sha256)
    return value


def registration_sha256(item: Target) -> str:
    return hashlib.sha256(canonical(registration_document(item))).hexdigest()


def _resolve(entries: tuple[Target, ...], target_id: str,
             *, synthetic: bool) -> Target:
    validate_registry(entries, synthetic=synthetic)
    matches = tuple(item for item in entries if item.target_id == target_id)
    if len(matches) != 1:
        raise ValueError("SA4 target is not compiled in the selected registry")
    return matches[0]


def resolve_production(target_id: str) -> Target:
    return _resolve(PRODUCTION_TARGETS, target_id, synthetic=False)


def resolve_schema_fixture(target_id: str) -> Target:
    return _resolve(SCHEMA_FIXTURES, target_id, synthetic=True)


validate_registry(SCHEMA_FIXTURES, synthetic=True)
validate_registry(PRODUCTION_TARGETS, synthetic=False)
