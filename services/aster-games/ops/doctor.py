#!/usr/bin/env python3
"""Content-silent health summary for HomeLab Doctor integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import urllib.error
import urllib.request


def probe(name: str, url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"name": name, "ok": 200 <= response.status < 300, "status": response.status}
    except urllib.error.HTTPError as error:
        return {"name": name, "ok": False, "status": error.code}
    except (urllib.error.URLError, TimeoutError):
        return {"name": name, "ok": False, "status": "unreachable"}


def container_health(name: str) -> dict:
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", name],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        status = "unreachable"
    return {"name": name, "ok": status == "healthy", "status": status}


def storage_health(path: Path, minimum_free_gib: int) -> dict:
    try:
        usage = shutil.disk_usage(path)
        free_gib = usage.free // (1024**3)
        ok = free_gib >= minimum_free_gib
        return {"name": path.name, "ok": ok, "free_gib": free_gib}
    except OSError:
        return {"name": path.name, "ok": False, "status": "unreachable"}


def policy_health(config_path: Path, gate_path: Path) -> dict:
    try:
        settings = json.loads(config_path.read_text(encoding="utf-8"))["settings"]
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        indexers_disabled = all(not item.get("enable", False) for item in settings["indexers"])
        downloaders_disabled = all(
            not item.get("enable", False) for item in settings["download_clients"]
        )
        closed = not gate.get("v4_client_work_allowed", True)
        ok = (
            not settings.get("auto_import", False)
            and indexers_disabled
            and downloaders_disabled
            and closed
        )
        return {
            "name": "safety-policy",
            "ok": ok,
            "acquisition_enabled": not (indexers_disabled and downloaders_disabled),
            "auto_import": bool(settings.get("auto_import", False)),
            "v4_client_work_allowed": bool(gate.get("v4_client_work_allowed", False)),
        }
    except (KeyError, OSError, TypeError, ValueError):
        return {"name": "safety-policy", "ok": False, "status": "invalid"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--romm", default="http://192.168.20.38:8080/api/heartbeat")
    parser.add_argument("--romarr", default="http://192.168.20.38:6868/api/health")
    parser.add_argument("--config", type=Path,
                        default=Path("/srv/aster-games/state/romarr/romarr.json"))
    parser.add_argument("--gate", type=Path,
                        default=Path("/opt/aster-games/config/release-gate.json"))
    parser.add_argument("--library", type=Path,
                        default=Path("/srv/aster-games/library"))
    parser.add_argument("--state", type=Path,
                        default=Path("/srv/aster-games/state"))
    parser.add_argument("--broker-container", default="aster-games-broker-1")
    parser.add_argument("--database-container", default="aster-games-romm-db-1")
    parser.add_argument("--cache-container", default="aster-games-romm-cache-1")
    parser.add_argument("--library-min-free-gib", type=int, default=100)
    parser.add_argument("--state-min-free-gib", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    results = [
        probe("romm", args.romm, args.timeout),
        probe("romarr", args.romarr, args.timeout),
        container_health(args.broker_container),
        container_health(args.database_container),
        container_health(args.cache_container),
        storage_health(args.library, args.library_min_free_gib),
        storage_health(args.state, args.state_min_free_gib),
        policy_health(args.config, args.gate),
    ]
    output = {"ok": all(result["ok"] for result in results), "services": results}
    print(json.dumps(output, sort_keys=True))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

