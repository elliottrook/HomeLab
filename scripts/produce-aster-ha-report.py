#!/usr/bin/env python3
"""Produce a strict aggregate HA report via the local Proxmox guest agent."""

from __future__ import annotations
import json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

REPORT_PATH = Path(os.environ.get("ASTER_HA_REPORT_PATH", "/var/lib/aster-ha-report/latest.json"))

def guest(command: list[str]) -> dict:
    outer = json.loads(subprocess.run(["qm", "guest", "exec", "103", "--", "ha", "--raw-json", *command], check=True, capture_output=True, text=True).stdout)
    if outer.get("exitcode") != 0: raise RuntimeError("guest command failed")
    inner = json.loads(outer.get("out-data", ""))
    if inner.get("result") != "ok" or not isinstance(inner.get("data"), dict): raise RuntimeError("invalid guest response")
    return inner["data"]

def build() -> dict:
    core = guest(["core", "info"]); supervisor = guest(["supervisor", "info"])
    mounts = guest(["mounts", "info"]); resolution = guest(["resolution", "info"])
    backup_mounts = [m for m in mounts.get("mounts", []) if isinstance(m, dict) and m.get("usage") == "backup"]
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "core": {"status": "healthy" if core.get("boot") else "failed", "version": str(core.get("version", "unknown"))[:32], "latest_version": str(core.get("version_latest", "unknown"))[:32], "update_available": bool(core.get("update_available")), "watchdog": bool(core.get("watchdog"))},
            "supervisor": {"status": "healthy" if supervisor.get("healthy") else "failed", "version": str(supervisor.get("version", "unknown"))[:32], "latest_version": str(supervisor.get("version_latest", "unknown"))[:32], "update_available": bool(supervisor.get("update_available")), "supported": bool(supervisor.get("supported")), "healthy": bool(supervisor.get("healthy"))},
            "backup": {"mount_configured": bool(backup_mounts), "mount_active": any(m.get("state") == "active" for m in backup_mounts)},
            "resolution": {"unsupported_count": len(resolution.get("unsupported", [])), "unhealthy_count": len(resolution.get("unhealthy", [])), "issue_count": len(resolution.get("issues", [])), "suggestion_count": len(resolution.get("suggestions", []))}}

def main():
    report = build(); REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".latest.", dir=REPORT_PATH.parent)
    try:
        with os.fdopen(fd, "w") as handle: json.dump(report, handle, separators=(",", ":")); handle.write("\n")
        os.chmod(tmp, 0o640); os.replace(tmp, REPORT_PATH)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

if __name__ == "__main__": main()
