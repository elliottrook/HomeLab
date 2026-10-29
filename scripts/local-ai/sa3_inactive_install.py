"""Fixed, inactive SA3 Proxmox/LXC110 installation transaction.

The transaction accepts one fixed staged packet and no caller-supplied target,
command, unit, service, schedule, credential or model.  Its default CLI is
deliberately a no-op; a separately authorized operator must pass ``--apply``.
Synthetic tests use :class:`LocalTarget`.  The live guest adapter uses only the
fixed ``pct exec 110`` helper below and never installs a persistent helper.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Callable, Iterable


PACKET_NAME = "ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json"
PACKET_SHA256 = "e4634c7724b8ac8c6b50689285a56f739ea16486f9fd3370f4b47e717ff36e6e"
EXPECTED_PLATFORM_COMMIT = "8dc6eac5"
EXPECTED_STREAM_COMMIT = "434c5aedddd59665c7e2e8961196b81310e02765"
HOST_CHECKPOINT = "/var/lib/local-ai-lab/checkpoints/sa3-inactive-install-8dc6eac5"
GUEST_CHECKPOINT = "/var/lib/local-ai-lab/checkpoints/sa3-inactive-install-8dc6eac5"
HOST_ROOT = "/usr/local/libexec/local-ai-lease/full-inference-pilot"
GUEST_ID = 110
STAGE_DEFAULT = "/var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5"


class InstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class FileSpec:
    target: str
    mode: int
    sha256: str
    source: str | None = None


@dataclass(frozen=True)
class FileState:
    target: str
    present: bool
    data: bytes = b""
    uid: int = 0
    gid: int = 0
    mode: int = 0
    nlink: int = 0

    @property
    def sha256(self) -> str | None:
        return hashlib.sha256(self.data).hexdigest() if self.present else None


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _regular_state(path: Path, target: str, *, expected_uid: int,
                   expected_mode: int | None = None) -> FileState:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return FileState(target=target, present=False)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != expected_uid
            or info.st_nlink != 1
            or (expected_mode is not None and stat.S_IMODE(info.st_mode) != expected_mode)):
        raise InstallError(f"TARGET_CUSTODY_INVALID:{target}")
    return FileState(target=target, present=True, data=path.read_bytes(),
                     uid=info.st_uid, gid=info.st_gid,
                     mode=stat.S_IMODE(info.st_mode), nlink=info.st_nlink)


def _directory_ok(path: Path, *, expected_uid: int, mode: int = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise InstallError(f"DIRECTORY_UNAVAILABLE:{path}") from exc
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != expected_uid
            or stat.S_IMODE(info.st_mode) != mode):
        raise InstallError(f"DIRECTORY_CUSTODY_INVALID:{path}")


def _write_once(path: Path, data: bytes, *, mode: int, uid: int, gid: int) -> None:
    parent = path.parent
    parent_info = parent.lstat()
    if not stat.S_ISDIR(parent_info.st_mode) or parent_info.st_uid != uid:
        raise InstallError(f"TARGET_PARENT_CUSTODY_INVALID:{parent}")
    temporary = parent / f".{path.name}.sa3-install-{os.getpid()}"
    if os.path.lexists(temporary):
        raise InstallError(f"TEMPORARY_TARGET_EXISTS:{temporary}")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        written = 0
        while written < len(data):
            written += os.write(descriptor, data[written:])
        os.fchmod(descriptor, mode)
        os.fchown(descriptor, uid, gid)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    directory_fd = os.open(parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    _regular_state(path, str(path), expected_uid=uid, expected_mode=mode)


class LocalTarget:
    """Rooted filesystem target used by the fixed host path and tests."""

    def __init__(self, root: Path, *, expected_uid: int):
        self.root = Path(root)
        self.expected_uid = expected_uid

    def path(self, target: str) -> Path:
        if not target.startswith("/"):
            raise InstallError(f"TARGET_NOT_ABSOLUTE:{target}")
        return self.root / target.lstrip("/")

    def inspect(self, target: str, *, mode: int | None = None) -> FileState:
        return _regular_state(self.path(target), target,
                              expected_uid=self.expected_uid, expected_mode=mode)

    def absent(self, target: str) -> None:
        path = self.path(target)
        if os.path.lexists(path):
            raise InstallError(f"PATH_MUST_BE_ABSENT:{target}")

    def checkpoint(self, targets: Iterable[FileSpec], checkpoint: str) -> None:
        root = self.path(checkpoint)
        if os.path.lexists(root):
            raise InstallError(f"CHECKPOINT_ALREADY_EXISTS:{checkpoint}")
        root.mkdir(parents=True, mode=0o700)
        os.chmod(root, 0o700)
        _directory_ok(root, expected_uid=self.expected_uid)
        states = []
        for spec in targets:
            state = self.inspect(spec.target, mode=spec.mode)
            states.append(state)
            payload = {
                "target": state.target, "present": state.present,
                "uid": state.uid, "gid": state.gid, "mode": state.mode,
                "nlink": state.nlink,
                "sha256": state.sha256,
                "data": base64.b64encode(state.data).decode() if state.present else "",
            }
            _write_once(root / (hashlib.sha256(spec.target.encode()).hexdigest() + ".json"),
                        _canonical(payload), mode=0o600,
                        uid=self.expected_uid, gid=os.getegid())
        _write_once(root / "manifest.json", _canonical({"targets": [s.target for s in states]}),
                    mode=0o600, uid=self.expected_uid, gid=os.getegid())

    def install(self, spec: FileSpec, data: bytes) -> None:
        path = self.path(spec.target)
        if not path.parent.exists():
            raise InstallError(f"TARGET_PARENT_MISSING:{spec.target}")
        _write_once(path, data, mode=spec.mode, uid=self.expected_uid, gid=os.getegid())

    def _checkpoint_states(self, targets: Iterable[FileSpec], checkpoint: str) -> list[FileState]:
        root = self.path(checkpoint)
        _directory_ok(root, expected_uid=self.expected_uid)
        manifest = _regular_state(root / "manifest.json", str(root / "manifest.json"),
                                  expected_uid=self.expected_uid, expected_mode=0o600)
        if not manifest.present:
            raise InstallError("CHECKPOINT_MANIFEST_MISSING")
        values = []
        for spec in targets:
            path = root / (hashlib.sha256(spec.target.encode()).hexdigest() + ".json")
            checkpoint_state = _regular_state(path, str(path), expected_uid=self.expected_uid,
                                              expected_mode=0o600)
            if not checkpoint_state.present:
                raise InstallError(f"CHECKPOINT_ENTRY_MISSING:{spec.target}")
            state = json.loads(checkpoint_state.data.decode("utf-8"))
            if state.get("target") != spec.target:
                raise InstallError(f"CHECKPOINT_ENTRY_MISMATCH:{spec.target}")
            values.append(FileState(
                target=state["target"], present=state["present"],
                data=base64.b64decode(state["data"]) if state["present"] else b"",
                uid=state["uid"], gid=state["gid"], mode=state["mode"], nlink=state["nlink"]))
        return values

    def rollback(self, targets: Iterable[FileSpec], checkpoint: str,
                 expected_new: dict[str, str]) -> None:
        for state in self._checkpoint_states(targets, checkpoint):
            current = self.inspect(state.target, mode=None)
            if current.present and current.sha256 not in {state.sha256, expected_new[state.target]}:
                raise InstallError(f"ROLLBACK_UNCERTAIN:{state.target}")
            if state.present:
                _write_once(self.path(state.target), state.data, mode=state.mode,
                            uid=self.expected_uid, gid=os.getegid())
            elif current.present:
                self.path(state.target).unlink()
            restored = self.inspect(state.target, mode=state.mode if state.present else None)
            if restored.present != state.present or (state.present and restored.data != state.data):
                raise InstallError(f"ROLLBACK_VERIFY_FAILED:{state.target}")

    def postcheck(self, files: Iterable[FileSpec], *, excluded: Iterable[str] = (),
                  units: Iterable[str] = ()) -> None:
        for spec in files:
            state = self.inspect(spec.target, mode=spec.mode)
            if not state.present or state.sha256 != spec.sha256:
                raise InstallError(f"POSTCHECK_HASH_FAILED:{spec.target}")
        for target in excluded:
            self.absent(target)
        for target in units:
            self.absent(target)


REMOTE_HELPER = r'''import base64, hashlib, json, os, stat, sys
from pathlib import Path

def fail(message):
    raise SystemExit(message)

def state(path):
    path = Path(path)
    try: info = path.lstat()
    except FileNotFoundError: return {"target": str(path), "present": False}
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1:
        fail("TARGET_CUSTODY_INVALID:" + str(path))
    data = path.read_bytes()
    return {"target": str(path), "present": True, "uid": info.st_uid,
            "gid": info.st_gid, "mode": stat.S_IMODE(info.st_mode),
            "nlink": info.st_nlink, "sha256": hashlib.sha256(data).hexdigest(),
            "data": base64.b64encode(data).decode()}

def atomic(path, data, mode):
    path = Path(path); parent = path.parent
    info = parent.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0: fail("PARENT_CUSTODY_INVALID")
    temporary = parent / ("." + path.name + ".sa3-install")
    if os.path.lexists(temporary): fail("TEMPORARY_TARGET_EXISTS")
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data); os.fchmod(fd, mode); os.fchown(fd, 0, 0); os.fsync(fd)
    finally: os.close(fd)
    os.replace(temporary, path)
    fd = os.open(parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
    value = state(path)
    if value["mode"] != mode: fail("INSTALL_CUSTODY_FAILED")

def main():
    op = sys.argv[1]; value = json.loads(sys.argv[2])
    if op == "inspect": print(json.dumps(state(value["target"]), sort_keys=True)); return
    if op == "absent":
        if os.path.lexists(value["target"]): fail("PATH_MUST_BE_ABSENT:" + value["target"])
        print("{}"); return
    if op == "install":
        atomic(value["target"], base64.b64decode(value["data"]), int(value["mode"], 8))
        print(json.dumps(state(value["target"]), sort_keys=True)); return
    if op == "remove":
        if os.path.lexists(value["target"]): os.unlink(value["target"])
        if os.path.lexists(value["target"]): fail("REMOVE_FAILED")
        print("{}"); return
    if op == "checkpoint":
        root = Path(value["checkpoint"])
        if os.path.lexists(root): fail("CHECKPOINT_ALREADY_EXISTS")
        root.mkdir(parents=True, mode=0o700); os.chmod(root, 0o700); os.chown(root, 0, 0)
        records = []
        for target in value["targets"]:
            record = state(target); records.append(record)
            (root / (hashlib.sha256(target.encode()).hexdigest() + ".json")).write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
            os.chown(root / (hashlib.sha256(target.encode()).hexdigest() + ".json"), 0, 0)
            os.chmod(root / (hashlib.sha256(target.encode()).hexdigest() + ".json"), 0o600)
        print(json.dumps({"targets": records}, sort_keys=True)); return
    if op == "postcheck":
        for record in value["files"]:
            current = state(record["target"])
            if not current.get("present") or current["sha256"] != record["sha256"] or current["mode"] != int(record["mode"], 8): fail("POSTCHECK_HASH_FAILED")
        for target in value["excluded"] + value["units"]:
            if os.path.lexists(target): fail("PATH_MUST_BE_ABSENT:" + target)
        sys.path.insert(0, value["runtime_root"])
        for name in value["imports"]: __import__(name)
        print("{}"); return
    if op == "rollback":
        root = Path(value["checkpoint"])
        for target in value["targets"]:
            record = json.loads((root / (hashlib.sha256(target.encode()).hexdigest() + ".json")).read_text(encoding="utf-8"))
            current = state(target)
            expected = value["expected_new"][target]
            if current.get("present") and current.get("sha256") not in {record.get("sha256"), expected}: fail("ROLLBACK_UNCERTAIN:" + target)
            if record.get("present"):
                atomic(target, base64.b64decode(record["data"]), int(record["mode"]))
            elif current.get("present"):
                os.unlink(target)
            restored = state(target)
            if restored.get("present") != record.get("present") or (record.get("present") and restored.get("sha256") != record.get("sha256")): fail("ROLLBACK_VERIFY_FAILED:" + target)
        print("{}"); return
    fail("UNKNOWN_OPERATION")

main()
'''


class PctTarget:
    """Fixed LXC110 adapter; the caller cannot provide a command."""

    def __init__(self, runner: Callable[..., object] = subprocess.run,
                 *, vmid: int = GUEST_ID):
        if vmid != GUEST_ID:
            raise InstallError("GUEST_ID_FIXED")
        self.runner = runner
        self.vmid = vmid

    def _call(self, operation: str, value: dict[str, object]) -> dict[str, object]:
        command = ("pct", "exec", str(self.vmid), "--", "/usr/bin/python3", "-B",
                   "-c", REMOTE_HELPER, operation,
                   json.dumps(value, sort_keys=True, separators=(",", ":")))
        result = self.runner(command, capture_output=True, text=True,
                             timeout=60, check=False)
        if result.returncode != 0:
            raise InstallError(f"LXC110_{operation.upper()}_FAILED:{result.stderr[-200:]}")
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise InstallError(f"LXC110_{operation.upper()}_MALFORMED") from exc

    def inspect(self, target: str, *, mode: int | None = None) -> FileState:
        value = self._call("inspect", {"target": target})
        if not value.get("present"):
            return FileState(target=target, present=False)
        if value.get("uid") != 0 or value.get("nlink") != 1 or (mode is not None and value.get("mode") != mode):
            raise InstallError(f"TARGET_CUSTODY_INVALID:{target}")
        return FileState(target=target, present=True,
                         data=base64.b64decode(value["data"]), uid=value["uid"],
                         gid=value["gid"], mode=value["mode"], nlink=value["nlink"])

    def absent(self, target: str) -> None:
        self._call("absent", {"target": target})

    def checkpoint(self, targets: Iterable[FileSpec], checkpoint: str) -> None:
        self._call("checkpoint", {"checkpoint": checkpoint,
                                   "targets": [s.target for s in targets]})

    def install(self, spec: FileSpec, data: bytes) -> None:
        self._call("install", {"target": spec.target, "mode": f"{spec.mode:04o}",
                                "data": base64.b64encode(data).decode()})

    def rollback(self, targets: Iterable[FileSpec], checkpoint: str,
                 expected_new: dict[str, str]) -> None:
        self._call("rollback", {"checkpoint": checkpoint,
                                 "targets": [s.target for s in targets],
                                 "expected_new": expected_new})

    def postcheck(self, files: Iterable[FileSpec], *, excluded: Iterable[str] = (),
                  units: Iterable[str] = (), runtime_root: str = "",
                  imports: Iterable[str] = ()) -> None:
        self._call("postcheck", {"files": [{"target": s.target, "mode": f"{s.mode:04o}", "sha256": s.sha256} for s in files],
                                  "excluded": list(excluded), "units": list(units),
                                  "runtime_root": runtime_root, "imports": list(imports)})


def _source_record(packet: dict[str, object], stage_root: Path,
                   source: str, expected: str, *, expected_uid: int) -> bytes:
    path = stage_root / source
    try:
        info = path.lstat()
    except OSError as exc:
        raise InstallError(f"STAGED_SOURCE_MISSING:{source}") from exc
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != expected_uid
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o644):
        raise InstallError(f"STAGED_SOURCE_CUSTODY_INVALID:{source}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise InstallError(f"STAGED_SOURCE_HASH_INVALID:{source}")
    return data


def _load_packet(stage_root: Path, *, expected_uid: int) -> dict[str, object]:
    _directory_ok(stage_root, expected_uid=expected_uid)
    packet_path = stage_root / "services/local-ai-lease" / PACKET_NAME
    info = packet_path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != expected_uid
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600):
        raise InstallError("PACKET_CUSTODY_INVALID")
    raw = packet_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PACKET_SHA256:
        raise InstallError("PACKET_HASH_INVALID")
    value = json.loads(raw)
    if (value.get("schema") != "aster-lab-hours-sa3-inactive-install.v1"
            or value.get("status") != "candidate-only"
            or value.get("effects_enabled") is not False
            or value.get("source_commits") != {"platform": EXPECTED_PLATFORM_COMMIT,
                                                "stream_a": EXPECTED_STREAM_COMMIT}):
        raise InstallError("PACKET_IDENTITY_INVALID")
    return value


def _records(packet: dict[str, object], stage_root: Path, *, expected_uid: int) -> tuple[list[FileSpec], list[FileSpec], dict[str, bytes], dict[str, bytes]]:
    host_specs = []
    guest_specs = []
    host_data: dict[str, bytes] = {}
    guest_data: dict[str, bytes] = {}
    for record in packet["host"]["install_files"]:
        spec = FileSpec(HOST_ROOT + "/" + record["target"], int(record["mode"], 8), record["sha256"], record["source"])
        host_specs.append(spec); host_data[spec.target] = _source_record(packet, stage_root, spec.source, spec.sha256, expected_uid=expected_uid)
    for record in packet["guest"]["runtime_files"]:
        spec = FileSpec(packet["guest"]["target_root"] + "/" + record["target"], int(record["mode"], 8), record["sha256"], record["source"])
        guest_specs.append(spec); guest_data[spec.target] = _source_record(packet, stage_root, spec.source, spec.sha256, expected_uid=expected_uid)
    wrapper = packet["guest"]["wrapper"]
    wrapper_spec = FileSpec(wrapper["target"], int(wrapper["mode"], 8), wrapper["sha256"], wrapper["source"])
    guest_specs.append(wrapper_spec); guest_data[wrapper_spec.target] = _source_record(packet, stage_root, wrapper_spec.source, wrapper_spec.sha256, expected_uid=expected_uid)
    return host_specs, guest_specs, host_data, guest_data


def _host_existing(packet: dict[str, object], target: LocalTarget) -> None:
    for record in packet["host"]["required_existing_pins"]:
        spec = FileSpec(HOST_ROOT + "/" + record["target"], int(record["mode"], 8), record["sha256"])
        state = target.inspect(spec.target, mode=spec.mode)
        if not state.present or state.sha256 != spec.sha256:
            raise InstallError(f"EXISTING_PIN_INVALID:{spec.target}")
    runner_state = target.inspect(HOST_ROOT + "/lab_hours_reserved_runner.py", mode=0o644)
    if b"WORKLOAD_RUNNER_UNAVAILABLE" not in runner_state.data:
        raise InstallError("FAIL_CLOSED_GATE_MISSING")


def _rollback(targets: list[tuple[object, list[FileSpec], str, dict[str, str]]]) -> None:
    errors = []
    for target, specs, checkpoint, expected_new in reversed(targets):
        try:
            target.rollback(specs, checkpoint, expected_new)
        except Exception as exc:
            errors.append(str(exc))
    if errors:
        raise InstallError("ROLLBACK_UNCERTAIN:" + ";".join(errors))


def install(stage_root: Path, *, host: LocalTarget | None = None,
            guest: PctTarget | LocalTarget | None = None,
            expected_uid: int = 0) -> dict[str, object]:
    if expected_uid != 0 and host is None and guest is None:
        raise InstallError("ROOT_REQUIRED")
    stage_root = Path(stage_root)
    packet = _load_packet(stage_root, expected_uid=expected_uid)
    host_specs, guest_specs, host_data, guest_data = _records(packet, stage_root, expected_uid=expected_uid)
    host = host or LocalTarget(Path("/"), expected_uid=expected_uid)
    guest = guest or PctTarget()
    host_units = packet["host"]["inactive_units"]
    guest_units = packet["guest"]["inactive_service_paths"]
    excluded = [packet["guest"]["target_root"] + "/" + name for name in packet["guest"]["excluded_runtime_files"]]
    for unit in host_units:
        host.absent(unit)
    for unit in guest_units:
        guest.absent(unit)
    for path in excluded:
        guest.absent(path)
    _host_existing(packet, host)
    completed_checkpoints: list[tuple[object, list[FileSpec], str, dict[str, str]]] = []
    try:
        host.checkpoint(host_specs, HOST_CHECKPOINT)
        completed_checkpoints.append((host, host_specs, HOST_CHECKPOINT,
                                      {s.target: s.sha256 for s in host_specs}))
        guest.checkpoint(guest_specs, GUEST_CHECKPOINT)
        completed_checkpoints.append((guest, guest_specs, GUEST_CHECKPOINT,
                                      {s.target: s.sha256 for s in guest_specs}))
        for spec in host_specs:
            host.install(spec, host_data[spec.target])
        for spec in guest_specs:
            guest.install(spec, guest_data[spec.target])
        host.postcheck(host_specs, units=host_units)
        _host_existing(packet, host)
        if isinstance(guest, LocalTarget):
            guest.postcheck(guest_specs, excluded=excluded, units=guest_units)
        else:
            guest.postcheck(guest_specs, excluded=excluded, units=guest_units,
                            runtime_root=packet["guest"]["target_root"],
                            imports=("sa3_expanded_quality_runner",))
        return {"state": "staged-candidate", "host_files": len(host_specs),
                "guest_files": len(guest_specs), "rollback": "checkpoint-retained",
                "effects": "not-attempted"}
    except BaseException as failure:
        if completed_checkpoints:
            try:
                _rollback(completed_checkpoints)
            except Exception as rollback_failure:
                raise rollback_failure from failure
        raise


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, default=Path(STAGE_DEFAULT))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply is required and separately authorized", "packet": PACKET_NAME}, sort_keys=True))
        return 2
    try:
        if os.geteuid() != 0:
            raise InstallError("ROOT_REQUIRED")
        print(json.dumps(install(args.stage_root), sort_keys=True))
        return 0
    except (InstallError, OSError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
