"""Fixed, content-free identity evidence for Aster gateway configuration.

Only two public runtime files are read from fixed paths. Their bytes and
individual digests never enter incident evidence. Secret-bearing environment,
credential and key files are outside this adapter's path set.
"""
from __future__ import annotations

import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_investigation import Observation


SOURCE = "aster-gateway-config-identity/v1"
CONFIG_PATHS = (
    Path("/etc/systemd/system/aster-agent.service"),
    Path("/opt/aster-agent/aster_agent.py"),
)
MAX_FILE_BYTES = 262_144


def _unavailable(incident_id: str, now: datetime) -> Observation:
    marker = hashlib.sha256((incident_id + "\0gateway-config-unavailable").encode()).hexdigest()[:24]
    return Observation(
        evidence_id="gateway-config-unavailable-" + marker,
        incident_id=incident_id,
        target="aster-gateway",
        kind="config",
        observed_at=now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        source=SOURCE,
        state="unavailable",
        summary="Registered Aster gateway configuration identity is unavailable.",
        facts={"reason": "source_unavailable"},
        truncated=False,
    )


def _digest_regular(path: Path, required_uid: int) -> bytes:
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != required_uid
            or metadata.st_mode & 0o022
            or metadata.st_size > MAX_FILE_BYTES
            or metadata.st_nlink != 1
        ):
            raise ValueError("unsafe configuration custody")
        raw = stream.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError("oversized configuration")
        return hashlib.sha256(raw).digest()


def read_gateway_config_observation(
    incident_id: str,
    now: datetime,
    *,
    paths: tuple[Path, ...] = CONFIG_PATHS,
    required_uid: int = 0,
) -> Observation:
    """Return only a combined digest for the fixed public runtime files."""
    try:
        if now.tzinfo is None or len(paths) != 2:
            raise ValueError("invalid request")
        combined = hashlib.sha256()
        for path in paths:
            combined.update(_digest_regular(path, required_uid))
        digest = combined.hexdigest()[:24]
        observed = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return Observation(
            evidence_id="gateway-config-" + digest,
            incident_id=incident_id,
            target="aster-gateway",
            kind="config",
            observed_at=observed,
            source=SOURCE,
            state="ok",
            summary="Registered Aster gateway configuration identity is available.",
            facts={"service": "aster-agent", "file_count": 2, "configuration_digest": digest},
            truncated=False,
        )
    except (OSError, ValueError, TypeError):
        return _unavailable(incident_id, now)
