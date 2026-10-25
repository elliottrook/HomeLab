"""Bounded, identity-bound watchdog for the Stream A evaluation lease.

The default CLI is inert.  Effectful mode accepts no caller-selected paths and
can only delegate restoration to the installed evaluation entrypoint.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from evaluation_lease import watchdog_decision
from evaluation_lease_adapter import AdapterState, read_state
from evaluation_lease_watchdog import run_bound_from_state


STATE_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/lease.json")
LOCK_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/lease.lock")
OPERATION_LOCK_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/lease.operation.lock")
HEARTBEAT_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/owner-heartbeat.json")
STATUS_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/watchdog-status.json")
IDENTITY_PATH = Path("/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json")
RESTORE_INTENT_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/restore-intent.json")
ENTRYPOINT = Path("/usr/local/sbin/stream-a-evaluation-lease")
OBSERVE_ENTRYPOINT = Path("/usr/local/sbin/stream-a-evaluation-restore-observe")


class WatchdogBoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class WatchdogIdentity:
    lease_id: str
    generation: int
    heartbeat_timeout: int
    owner_id: str
    pid: int
    boot_id: str
    starttime_ticks: int
    cmdline: str
    unit: str


@dataclass(frozen=True)
class OwnerHeartbeat:
    lease_id: str
    generation: int
    owner_id: str
    heartbeat_epoch: int
    expires_epoch: int
    pid: int
    boot_id: str
    starttime_ticks: int
    cmdline: str
    unit: str


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise WatchdogBoundaryError("duplicate JSON key")
        result[key] = value
    return result


def _read_root_json(path: Path, keys: set[str], *, required_uid: int = 0) -> dict[str, object]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise WatchdogBoundaryError("root-owned descriptor cannot be opened") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != required_uid
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise WatchdogBoundaryError("descriptor custody is not root-owned 0600")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            value = json.load(stream, object_pairs_hook=_unique_pairs)
    finally:
        if fd != -1:
            os.close(fd)
    if not isinstance(value, dict) or set(value) != keys:
        raise WatchdogBoundaryError("descriptor schema is not exact")
    return value


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise WatchdogBoundaryError(f"{name} is invalid")
    return value


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise WatchdogBoundaryError(f"{name} is invalid")
    return value


def load_identity(path: Path = IDENTITY_PATH, *, required_uid: int = 0) -> WatchdogIdentity:
    value = _read_root_json(path, {"lease_id", "generation", "heartbeat_timeout", "owner_id",
                                   "pid", "boot_id", "starttime_ticks", "cmdline", "unit"},
                            required_uid=required_uid)
    generation = _integer(value["generation"], "generation")
    timeout = _integer(value["heartbeat_timeout"], "heartbeat_timeout")
    pid = _integer(value["pid"], "pid")
    starttime = _integer(value["starttime_ticks"], "starttime_ticks")
    if generation < 1 or timeout < 1 or pid < 1 or starttime < 1:
        raise WatchdogBoundaryError("identity bounds are invalid")
    return WatchdogIdentity(_nonempty(value["lease_id"], "lease_id"), generation,
                            timeout, _nonempty(value["owner_id"], "owner_id"), pid,
                            _nonempty(value["boot_id"], "boot_id"), starttime,
                            _nonempty(value["cmdline"], "cmdline"),
                            _nonempty(value["unit"], "unit"))


def load_owner_heartbeat(path: Path = HEARTBEAT_PATH, *, identity: WatchdogIdentity,
                         now_epoch: int, required_uid: int = 0) -> OwnerHeartbeat:
    value = _read_root_json(path, {"lease_id", "generation", "owner_id",
                                   "heartbeat_epoch", "expires_epoch", "pid", "boot_id",
                                   "starttime_ticks", "cmdline", "unit"}, required_uid=required_uid)
    heartbeat = OwnerHeartbeat(
        _nonempty(value["lease_id"], "lease_id"),
        _integer(value["generation"], "generation"),
        _nonempty(value["owner_id"], "owner_id"),
        _integer(value["heartbeat_epoch"], "heartbeat_epoch"),
        _integer(value["expires_epoch"], "expires_epoch"),
        _integer(value["pid"], "pid"), _nonempty(value["boot_id"], "boot_id"),
        _integer(value["starttime_ticks"], "starttime_ticks"),
        _nonempty(value["cmdline"], "cmdline"), _nonempty(value["unit"], "unit"),
    )
    if (heartbeat.lease_id != identity.lease_id
            or heartbeat.generation != identity.generation
            or heartbeat.owner_id != identity.owner_id
            or (heartbeat.pid, heartbeat.boot_id, heartbeat.starttime_ticks,
                heartbeat.cmdline, heartbeat.unit)
            != (identity.pid, identity.boot_id, identity.starttime_ticks,
                identity.cmdline, identity.unit)
            or heartbeat.heartbeat_epoch > now_epoch
            or heartbeat.expires_epoch <= heartbeat.heartbeat_epoch
            or heartbeat.expires_epoch - heartbeat.heartbeat_epoch > identity.heartbeat_timeout):
        raise WatchdogBoundaryError("owner heartbeat is foreign, stale or overlong")
    return heartbeat


def write_owner_heartbeat(path: Path, *, identity: WatchdogIdentity,
                          now_epoch: int) -> None:
    if os.geteuid() != 0:
        raise WatchdogBoundaryError("owner heartbeat requires root")
    if not owner_process_matches(identity):
        raise WatchdogBoundaryError("owner process identity is absent or reused")
    payload = {"lease_id": identity.lease_id, "generation": identity.generation,
               "owner_id": identity.owner_id, "heartbeat_epoch": now_epoch,
               "expires_epoch": now_epoch + identity.heartbeat_timeout,
               "pid": identity.pid, "boot_id": identity.boot_id,
               "starttime_ticks": identity.starttime_ticks, "cmdline": identity.cmdline,
               "unit": identity.unit}
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _baseline_json(state: AdapterState) -> dict[str, list[list[str]]]:
    return {"units": [list(item) for item in state.baseline.units],
            "timers": [list(item) for item in state.baseline.timers]}


def owner_process_matches(identity: WatchdogIdentity, *, snapshot: Callable[[WatchdogIdentity], dict[str, object]] | None = None) -> bool:
    if snapshot is not None:
        try:
            value = snapshot(identity)
        except (OSError, ValueError):
            return False
        return value == {"boot_id": identity.boot_id, "starttime_ticks": identity.starttime_ticks,
                         "cmdline": identity.cmdline, "unit": identity.unit}
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        raw = Path(f"/proc/{identity.pid}/stat").read_text()
        tail = raw[raw.rfind(")") + 2:].split()
        starttime = int(tail[19])
        cmdline = Path(f"/proc/{identity.pid}/cmdline").read_bytes().replace(b"\0", b" ").decode().strip()
        cgroup = Path(f"/proc/{identity.pid}/cgroup").read_text()
        return (boot_id == identity.boot_id and starttime == identity.starttime_ticks
                and cmdline == identity.cmdline and identity.unit in cgroup)
    except (OSError, ValueError, UnicodeError):
        return False


def _restore_callback(state: AdapterState, *, intent_path: Path,
                      runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> object:
    observed = runner((str(OBSERVE_ENTRYPOINT), "--lease-id", state.lease_id,
                       "--generation", str(state.generation)), check=False,
                      capture_output=True, text=True, timeout=30)
    if observed.returncode != 0:
        raise WatchdogBoundaryError("live restore observer failed")
    try:
        observation = json.loads(observed.stdout)
    except json.JSONDecodeError as exc:
        raise WatchdogBoundaryError("live restore observer output is malformed") from exc
    if not isinstance(observation, dict) or set(observation) != {
            "lease_id", "generation", "observed_at", "backend_active",
            "endpoint_authenticated", "endpoint_idle", "gpu_holders"}:
        raise WatchdogBoundaryError("live restore observer schema is not exact")
    if (observation["lease_id"] != state.lease_id
            or observation["generation"] != state.generation
            or type(observation["observed_at"]) is not int
            or abs(int(time.time()) - observation["observed_at"]) > 15):
        raise WatchdogBoundaryError("live restore observation is stale")
    for key in ("backend_active", "endpoint_authenticated", "endpoint_idle"):
        if type(observation[key]) is not bool:
            raise WatchdogBoundaryError("restore observation boolean is invalid")
    holders = observation["gpu_holders"]
    if not isinstance(holders, list) or any(not isinstance(item, str) for item in holders):
        raise WatchdogBoundaryError("restore observation GPU holder list is invalid")
    payload = {
        "lease_id": state.lease_id, "generation": state.generation,
        "restored_baseline": _baseline_json(state),
        "backend_active": observation["backend_active"],
        "endpoint_authenticated": observation["endpoint_authenticated"],
        "endpoint_idle": observation["endpoint_idle"],
        "gpu_holders": holders, "recovery": True,
    }
    intent_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{intent_path.name}.", dir=intent_path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, intent_path)
        result = runner((str(ENTRYPOINT), "--phase", "restore", "--state", str(STATE_PATH),
                         "--intent", str(intent_path), "--effect-authorized"),
                        check=False, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise WatchdogBoundaryError("installed restore entrypoint failed")
        return {"entrypoint": "restored", "stdout": result.stdout[-512:]}
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run_watchdog_once(*, state_path: Path = STATE_PATH, identity_path: Path = IDENTITY_PATH,
                      heartbeat_path: Path = HEARTBEAT_PATH, now_epoch: int,
                      effect_authorized: bool, recovery: Callable[[AdapterState], object] | None = None) -> dict[str, object]:
    if not effect_authorized:
        return {"effects": "disabled", "state": "source-only"}
    try:
        identity = load_identity(identity_path)
        state = read_state(state_path, expected_lease_id=identity.lease_id,
                           expected_generation=identity.generation)
        owner_present = True
        try:
            heartbeat = load_owner_heartbeat(heartbeat_path, identity=identity, now_epoch=now_epoch)
            owner_present = now_epoch < heartbeat.expires_epoch
        except WatchdogBoundaryError:
            try:
                heartbeat_path.lstat()
            except FileNotFoundError:
                owner_present = False
            else:
                raise
        result = run_bound_from_state(
            path=state_path, expected_lease_id=identity.lease_id,
            expected_generation=identity.generation, now_epoch=now_epoch,
            heartbeat_timeout=identity.heartbeat_timeout,
            owner_present=owner_present, effect_authorized=True,
            recovery=(lambda: recovery(state)) if recovery is not None else None,
        )
        return result
    except (OSError, ValueError, WatchdogBoundaryError) as exc:
        return {"effects": "failed-closed", "error": type(exc).__name__}


def write_status(result: dict[str, object], path: Path = STATUS_PATH) -> None:
    allowed = {"effects", "decision", "error"}
    payload = {key: result[key] for key in result if key in allowed}
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
        return 0
    if os.geteuid() != 0:
        print(json.dumps({"effects": "failed-closed", "error": "root-required"}, sort_keys=True))
        return 1
    result = run_watchdog_once(
        now_epoch=int(time.time()), effect_authorized=True,
        recovery=lambda state: _restore_callback(
            state, intent_path=RESTORE_INTENT_PATH),
    )
    write_status(result)
    print(json.dumps(result, sort_keys=True))
    return 1 if result.get("effects") in {"failed-closed", "uncertain"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
