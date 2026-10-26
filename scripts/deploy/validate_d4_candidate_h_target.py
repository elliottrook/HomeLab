#!/usr/bin/python3
"""Content-free target validation for an inactive D4 candidate-H install."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess


LAUNCHER = Path("/usr/local/libexec/aster-d4-candidate-h-launcher")
UNIT = "aster-d4-candidate-h.service"
FICTIONAL_SECRET = bytearray(b"fictional-target-validation-key")


def service_state() -> tuple[str, str]:
    active = subprocess.run(
        ["systemctl", "show", UNIT, "--property=ActiveState", "--value"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    enabled_probe = subprocess.run(
        ["systemctl", "is-enabled", UNIT], capture_output=True, text=True,
    )
    enabled = enabled_probe.stdout.strip()
    if active != "inactive" or enabled not in {"disabled", "static"}:
        raise RuntimeError("candidate service is not inactive and unenabled")
    return active, enabled


def load_launcher():
    spec = importlib.util.spec_from_file_location("d4_candidate_h_launcher", LAUNCHER)
    if spec is None or spec.loader is None:
        raise RuntimeError("candidate launcher import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def child_probe_source() -> str:
    return r'''
import os
from pathlib import Path
import sys

fd = int(sys.argv[-1])
secret = os.read(fd, 4097)
os.close(fd)
ok = (
    os.getuid() == 977
    and os.getgid() == 977
    and os.getgroups() == []
    and secret == b"fictional-target-validation-key"
    and "ASTER_LLAMA_API_KEY" not in os.environ
)
packet = Path("/var/lib/aster/d4-candidate-h")
files = list(packet.iterdir())
ok = ok and len(files) == 11 and all(path.is_file() and path.read_bytes() for path in files)
try:
    (packet / ".write-probe").write_bytes(b"fictional")
    ok = False
except PermissionError:
    pass
try:
    Path("/etc/aster/aster.env").read_bytes()
    ok = False
except PermissionError:
    pass
output = Path("/var/lib/aster/d4-candidate-h-output")
probe = output / ".fictional-custody-probe"
try:
    descriptor = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(descriptor, b"fictional")
    os.close(descriptor)
    metadata = probe.stat()
    ok = ok and metadata.st_uid == 977 and metadata.st_gid == 977
finally:
    try:
        probe.unlink()
    except FileNotFoundError:
        pass
raise SystemExit(0 if ok else 19)
'''


def validate() -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("root target validation identity required")
    before = service_state()
    launcher = load_launcher()
    eval_uid, eval_gid = launcher.validate_eval_identity()
    launcher.validate_packet(gid=eval_gid)
    launcher.validate_output_directory(uid=eval_uid, gid=eval_gid)
    launcher.validate_interpreter()
    result = launcher.run_with_key_fd(
        [str(launcher.INTERPRETER), "-c", child_probe_source()],
        FICTIONAL_SECRET,
        timeout=30,
        child_uid=eval_uid,
        child_gid=eval_gid,
    )
    if result != 0:
        raise RuntimeError("fictional dedicated-identity probe failed")
    launcher.validate_output_directory(uid=eval_uid, gid=eval_gid)
    after = service_state()
    if after != before:
        raise RuntimeError("candidate service state changed during validation")
    return {
        "status": "pass",
        "uid": eval_uid,
        "gid": eval_gid,
        "supplementary_groups": 0,
        "packet_files": len(launcher.FILES),
        "credential_read": False,
        "model_calls": 0,
        "output_empty": True,
        "service_active": before[0],
        "service_enablement": before[1],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
