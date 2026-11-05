#!/usr/bin/env python3
"""Install the inert, registered M5B eBook alignment workload on Proxmox.

The installer changes registration only.  It never creates a booking, starts a
workload, enables a timer or runs a model.  Exact source hashes and single-use
text anchors make an unknown platform revision fail closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time


PILOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
REGISTRY = PILOT / "lab_hours_workloads.py"
RUNNER = PILOT / "lab_hours_reserved_runner.py"
RUNTIME = PILOT / "full_inference_lab_runtime.py"
MANIFEST = PILOT / "lab_hours_release_manifest.json"
BASE_PINS = {
    REGISTRY: "3cd767b3cc0aa9d590821a7e24e7675c6a3ca5a29907317ba98ef6739031ed98",
    RUNNER: "68d1c24d2ba440068533c694ab773462d3bff3442a4276be852ffafb78625542",
    RUNTIME: "1760fa046156d7a8268a9e7fbf52c06eac2df9690a2033d184afb8b6b2211c8c",
    MANIFEST: "3c12af56e18612c314fdcc4cc336064264d1593a74bc94e9980357ab5366d9e8",
}
WORKLOAD_ID = "astertv-v3-ebook-word-alignment-v1"
GUEST_TARGET = "/opt/epub-narration/tools/ebook_word_alignment_benchmark.py"
CHECKPOINT_ROOT = Path("/var/lib/local-ai-lab/checkpoints")


class InstallError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path, expected: str | None = None) -> bytes:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != 0
            or info.st_nlink != 1 or info.st_size > 2 * 1024 * 1024):
        raise InstallError("SOURCE_CUSTODY")
    data = path.read_bytes()
    if expected is not None and digest(data) != expected:
        raise InstallError("SOURCE_DRIFT:" + path.name)
    return data


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise InstallError("ANCHOR_DRIFT:" + label)
    return text.replace(old, new)


def transform_registry(source: str, transaction_sha: str, adapter_sha: str) -> str:
    entry_anchor = "\n}\n\n\nREGISTERED_WORKLOADS = frozenset(WORKLOADS)"
    entry = f'''\n    "{WORKLOAD_ID}": WorkloadSpec(\n        workload_id="{WORKLOAD_ID}", owner="astertv-v3-m5",\n        request_count=1, per_request_timeout_seconds=600, deadline_seconds=900,\n        minimum_booking_seconds=1800, recovery_reserve_seconds=900,\n        runner_kind="ebook-word-alignment", runtime_pins=(\n            ("epub_word_alignment_transaction.py", "{transaction_sha}"),\n            ("epub_word_alignment_adapter.py", "{adapter_sha}"),\n        ),\n        packet_sha256="1fde84377288795f522d5946380734e43dc643fd58b06720fdf79b56d59dd257",\n        result_max_bytes=65536,\n    ),\n}}\n\n\nREGISTERED_WORKLOADS = frozenset(WORKLOADS)'''
    source = replace_once(source, entry_anchor, entry, "registry-entry")
    validation_anchor = "\n\ndef _local_imports(path: Path) -> set[str]:"
    validation = f'''\n    ebook = workload("{WORKLOAD_ID}")\n    if (ebook.owner != "astertv-v3-m5"\n            or ebook.request_count != 1\n            or ebook.per_request_timeout_seconds != 600\n            or ebook.deadline_seconds != 900\n            or ebook.minimum_booking_seconds != 1800\n            or ebook.recovery_reserve_seconds != 900\n            or ebook.runner_kind != "ebook-word-alignment"\n            or len(ebook.runtime_pins) != 2\n            or ebook.packet_sha256 !=\n                "1fde84377288795f522d5946380734e43dc643fd58b06720fdf79b56d59dd257"\n            or ebook.result_max_bytes != 65536):\n        raise ValueError("eBook word-alignment registration drift")\n\n\ndef _local_imports(path: Path) -> set[str]:'''
    return replace_once(source, validation_anchor, validation, "registry-validation")


def transform_runtime(source: str) -> str:
    branch = '''    elif args.workload_profile == "sa3-evidence-matrix-candidate-j-public-v1":
        from sa3_candidate_j_evidence_matrix_transaction import execute
        from sa3_candidate_j_evidence_matrix_listener_adapter import run as run_sa3_listener
    else:'''
    branch_new = '''    elif args.workload_profile == "sa3-evidence-matrix-candidate-j-public-v1":
        from sa3_candidate_j_evidence_matrix_transaction import execute
        from sa3_candidate_j_evidence_matrix_listener_adapter import run as run_sa3_listener
    elif args.workload_profile == "astertv-v3-ebook-word-alignment-v1":
        from epub_word_alignment_transaction import execute
        from epub_word_alignment_adapter import run as run_sa3_listener
    else:'''
    source = replace_once(source, branch, branch_new, "runtime-import")
    duration = '''    lab_seconds = (1800 if args.workload_profile ==
                   "sa3-evidence-matrix-candidate-j-public-v1" else 2700)'''
    duration_new = '''    lab_seconds = (900 if args.workload_profile ==
                   "astertv-v3-ebook-word-alignment-v1" else
                   (1800 if args.workload_profile ==
                    "sa3-evidence-matrix-candidate-j-public-v1" else 2700))'''
    source = replace_once(source, duration, duration_new, "runtime-duration")
    cleanup = '''    def cleanup_postcheck() -> None:
        plan = captured.get("plan")
        if plan is None or not lab_is_absent(runner, lease_id=plan.lease_id,
                                             generation=plan.generation):
            raise SupervisorError("SA3 listener cleanup is not proven")
        _accepted_gpu_baseline(gpu_users())'''
    cleanup_new = '''    def cleanup_postcheck() -> None:
        plan = captured.get("plan")
        if plan is None:
            raise SupervisorError("workload plan was not captured")
        if args.workload_profile == "astertv-v3-ebook-word-alignment-v1":
            from epub_word_alignment_adapter import absent
            if not absent(runner, lease_id=plan.lease_id, generation=plan.generation):
                raise SupervisorError("eBook alignment cleanup is not proven")
        elif not lab_is_absent(runner, lease_id=plan.lease_id,
                               generation=plan.generation):
            raise SupervisorError("SA3 listener cleanup is not proven")
        _accepted_gpu_baseline(gpu_users())'''
    source = replace_once(source, cleanup, cleanup_new, "runtime-cleanup")
    choice = '''        "sa3-evidence-matrix-candidate-j-public-v1",
        "m3-joint-semantic-35b-public-v1"),'''
    choice_new = '''        "sa3-evidence-matrix-candidate-j-public-v1",
        "m3-joint-semantic-35b-public-v1",
        "astertv-v3-ebook-word-alignment-v1"),'''
    source = replace_once(source, choice, choice_new, "runtime-choice")
    route = '''                "sa3-evidence-envelope-candidate-i-quality-v1",
                "sa3-evidence-matrix-candidate-j-public-v1"}:
            return _run_sa3(args, paths, runner=runner)'''
    route_new = '''                "sa3-evidence-envelope-candidate-i-quality-v1",
                "sa3-evidence-matrix-candidate-j-public-v1",
                "astertv-v3-ebook-word-alignment-v1"}:
            return _run_sa3(args, paths, runner=runner)'''
    return replace_once(source, route, route_new, "runtime-route")


def transform_runner(source: str) -> str:
    kinds = '''    "m3-joint-semantic-35b",
})'''
    kinds_new = '''    "m3-joint-semantic-35b",
    "ebook-word-alignment",
})'''
    source = replace_once(source, kinds, kinds_new, "runner-kind")
    admission = '''        spec = workload(str(booking.get("workload")))
        if spec.runner_kind not in REGISTERED_RUNNER_KINDS:
            raise RunError("WORKLOAD_RUNNER_NOT_REGISTERED")'''
    admission_new = '''        spec = workload(str(booking.get("workload")))
        if spec.runner_kind not in REGISTERED_RUNNER_KINDS:
            raise RunError("WORKLOAD_RUNNER_NOT_REGISTERED")
        if spec.runner_kind == "ebook-word-alignment":
            if booking.get("owner") != spec.owner:
                raise RunError("WORKLOAD_OWNER_MISMATCH")
            if int(booking["end_epoch"]) - int(booking["start_epoch"]) < spec.minimum_booking_seconds:
                raise RunError("WORKLOAD_WINDOW_TOO_SHORT")'''
    source = replace_once(source, admission, admission_new, "runner-admission")
    effect = '''        expected_effect=("guardian-rescued" if expected_requests==0 else
                         ("sa3-expanded-quality-complete"
                          if spec.runner_kind=="sa3-expanded-quality" else
                          ("sa3-evidence-envelope-quality-complete"
                           if spec.runner_kind=="sa3-evidence-envelope-quality" else
                          ("sa3-evidence-envelope-candidate-i-quality-complete"
                           if spec.runner_kind=="sa3-evidence-envelope-candidate-i-quality" else
                          ("sa3-evidence-matrix-candidate-j-public-complete"
                           if spec.runner_kind=="sa3-evidence-matrix-candidate-j-public" else
                          ("m3-joint-semantic-public-complete"
                           if spec.runner_kind=="m3-joint-semantic-35b" else "pilot-complete"))))))'''
    effect_new = '''        expected_effect=("guardian-rescued" if expected_requests==0 else {
            "sa3-expanded-quality": "sa3-expanded-quality-complete",
            "sa3-evidence-envelope-quality": "sa3-evidence-envelope-quality-complete",
            "sa3-evidence-envelope-candidate-i-quality":
                "sa3-evidence-envelope-candidate-i-quality-complete",
            "sa3-evidence-matrix-candidate-j-public":
                "sa3-evidence-matrix-candidate-j-public-complete",
            "m3-joint-semantic-35b": "m3-joint-semantic-public-complete",
            "ebook-word-alignment": "ebook-word-alignment-benchmark-complete",
        }.get(spec.runner_kind, "pilot-complete"))'''
    source = replace_once(source, effect, effect_new, "runner-effect")
    receipt = '''        elif spec.runner_kind=="m3-joint-semantic-35b":
            receipt_valid=(receipt_valid'''
    receipt_new = '''        elif spec.runner_kind=="ebook-word-alignment":
            receipt_valid=(receipt_valid
                and set(receipt)=={"effects","production_restored","receipt"}
                and set(receipt_body)=={"exit_status","profile","request_count",
                                        "result_sha256","passed","failure_code",
                                        "measured_word_count"}
                and receipt.get("production_restored") is True
                and isinstance(receipt_body.get("result_sha256"),str)
                and len(receipt_body["result_sha256"])==64
                and all(c in "0123456789abcdef" for c in receipt_body["result_sha256"])
                and type(receipt_body.get("passed")) is bool
                and isinstance(receipt_body.get("failure_code"),str)
                and type(receipt_body.get("measured_word_count")) is int
                and 0 <= receipt_body["measured_word_count"] <= 4000)
        elif spec.runner_kind=="m3-joint-semantic-35b":
            receipt_valid=(receipt_valid'''
    return replace_once(source, receipt, receipt_new, "runner-receipt")


def build(stage: Path) -> dict[Path, bytes]:
    transaction = regular(stage / "epub_word_alignment_transaction.py")
    adapter = regular(stage / "epub_word_alignment_adapter.py")
    guest = regular(stage / "ebook_word_alignment_benchmark.py")
    if b"TO_BE_PINNED" in adapter:
        raise InstallError("ADAPTER_UNPINNED")
    sources = {path: regular(path, expected) for path, expected in BASE_PINS.items()}
    output = {
        REGISTRY: transform_registry(sources[REGISTRY].decode(), digest(transaction), digest(adapter)).encode(),
        RUNNER: transform_runner(sources[RUNNER].decode()).encode(),
        RUNTIME: transform_runtime(sources[RUNTIME].decode()).encode(),
        PILOT / "epub_word_alignment_transaction.py": transaction,
        PILOT / "epub_word_alignment_adapter.py": adapter,
    }
    manifest = json.loads(sources[MANIFEST])
    pins = manifest.get("pins")
    if not isinstance(pins, dict) or not pins:
        raise InstallError("MANIFEST_SCHEMA")
    for path, data in output.items():
        pins[path.name] = digest(data)
    output[MANIFEST] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    if digest(guest) not in adapter.decode():
        raise InstallError("GUEST_PIN_NOT_BOUND")
    return output


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    temporary = path.with_name("." + path.name + ".m5b-next")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, mode)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def call(command: tuple[str, ...], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    if os.geteuid() != 0 or os.uname().nodename != "proxmox":
        raise SystemExit("PROXMOX_ROOT_REQUIRED")
    output = build(args.stage)
    if not args.install:
        print(json.dumps({"state": "validated", "effects": "not-attempted",
                          "files": len(output), "workload": WORKLOAD_ID}, sort_keys=True))
        return 0
    worker = call(("pct", "exec", "116", "--", "systemctl", "is-active",
                   "epub-narration-worker.service"), 15)
    scheduler = call(("systemctl", "is-enabled", "epub-narration-scheduler.timer"), 15)
    lease = call(("/usr/local/sbin/local-ai-lease", "status"), 15)
    try:
        lease_value = json.loads(lease.stdout)
    except json.JSONDecodeError:
        lease_value = None
    if worker.returncode == 0 or scheduler.stdout.strip() != "disabled" or lease_value != {"state": "ready"}:
        raise InstallError("LIVE_PREFLIGHT")
    checkpoint = CHECKPOINT_ROOT / ("astertv-v3-m5b-registration-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    checkpoint.mkdir(mode=0o700, parents=True)
    for path in BASE_PINS:
        shutil.copy2(path, checkpoint / path.name)
        (checkpoint / path.name).chmod(0o600)
    guest = regular(args.stage / "ebook_word_alignment_benchmark.py")
    try:
        for path, data in output.items():
            atomic_write(path, data)
        staged_guest = Path("/tmp/astertv-v3-m5b-ebook-word-alignment.py")
        atomic_write(staged_guest, guest, 0o600)
        pushed = call(("pct", "push", "116", str(staged_guest), GUEST_TARGET, "--perms", "0755"), 30)
        staged_guest.unlink()
        if pushed.returncode != 0:
            raise InstallError("GUEST_INSTALL")
        checks = (
            ("/usr/bin/python3", "-B", "-c",
             "import sys; sys.path.insert(0,'/usr/local/libexec/local-ai-lease/full-inference-pilot'); import lab_hours_workloads as w; print(w.workload('astertv-v3-ebook-word-alignment-v1'))"),
            ("/usr/bin/python3", "-B", "-m", "py_compile",
             str(REGISTRY), str(RUNNER), str(RUNTIME),
             str(PILOT / "epub_word_alignment_transaction.py"),
             str(PILOT / "epub_word_alignment_adapter.py")),
            ("pct", "exec", "116", "--", "/opt/whisper-bench/bin/python", "-m", "py_compile", GUEST_TARGET),
        )
        for command in checks:
            checked = call(command, 60)
            if checked.returncode != 0:
                raise InstallError("STATIC_VALIDATION")
    except BaseException:
        for path in BASE_PINS:
            shutil.copy2(checkpoint / path.name, path)
        for name in ("epub_word_alignment_transaction.py", "epub_word_alignment_adapter.py"):
            target = PILOT / name
            if target.exists():
                target.unlink()
        call(("pct", "exec", "116", "--", "rm", "-f", GUEST_TARGET), 30)
        raise
    print(json.dumps({"state": "installed-inactive", "workload": WORKLOAD_ID,
                      "checkpoint": str(checkpoint), "booking_created": False,
                      "workload_started": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"state": "no_go", "code": str(error)}, sort_keys=True))
        raise SystemExit(1)
