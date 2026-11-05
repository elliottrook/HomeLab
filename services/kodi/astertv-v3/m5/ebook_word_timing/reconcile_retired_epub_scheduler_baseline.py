#!/usr/bin/env python3
"""Reconcile the full-drain controller with the retired EPUB scheduler.

The accepted baseline is: host scheduler disabled/inactive, guest worker timer
disabled/inactive, worker inactive/success, and the read-only monitor
enabled/active.  The full-drain controller must neither restore nor depend on
the retired scheduler.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import time


ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
MANIFEST = ROOT / "lab_hours_release_manifest.json"
PINS = {
    "full_inference_lab_sources.py": "c07c2966a13144b8ca2b68639917381bad7381f9d8fa61adc265f1b30f59c5d9",
    "full_inference_lab_session.py": "b3c38f030cbe1c0d45f59947cb2bc68cb7f80ed6410ef1669c88c18027296e9a",
    "full_inference_lab_install_preflight.py": "1ea2e37eb2ab8ea34251f4af1337cd2d7f94b00933eb60ff7433b6adbe6ca8d3",
    "test_cooperative_lab_host_adapter.py": "8464f82ec4ce813103d63764113894f0f258bf4617f94670d2679ab1a7d1e7e8",
    "test_full_inference_lab_install_preflight.py": "a36023cfeff27f839492db8c364a56713fa8f45669154a124f926427fded875b",
    "test_full_inference_lab_session.py": "86c9d5e3979647cfb212ec54288acb9df72a05d9a98d21daeaa620021daeb90c",
    "test_full_inference_lab_sources.py": "c5093895456cd07573636bcad85d8e31db9169877048cc848cfe91f475655b29",
    "test_full_inference_lab_supervisor.py": "80ddaebfd344042b68a585febd01c5d7029d17fe29519fed4cda94223936f665",
    "test_full_inference_lab_validator.py": "f362d599d7fceeda0f52257a4afd8fdbccdbea8b1538d44d5453bf60a17c2d2d",
    "lab_hours_release_manifest.json": "7d08d0254d49dbd68cd68f205ade30bea6b9d7d81607327dcb9fa392ac5e1100",
}
CHECKPOINTS = Path("/var/lib/local-ai-lab/checkpoints")


class ReconcileError(RuntimeError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(name: str) -> str:
    path = ROOT / name
    info = path.lstat()
    data = path.read_bytes()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != 0
            or info.st_nlink != 1 or sha(data) != PINS[name]):
        raise ReconcileError("SOURCE_DRIFT:" + name)
    return data.decode()


def once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise ReconcileError("ANCHOR_DRIFT:" + label)
    return text.replace(old, new)


def health(source: str) -> str:
    start = source.index("def epub_narration_healthy(")
    end = source.index("\n\n@dataclass", start)
    replacement = '''def epub_narration_healthy(run_command: Callable[[Sequence[str]], str]) -> bool:
    """Validate the retired-scheduler, registered-workload EPUB baseline."""
    scheduler = run_command(("systemctl", "show", "epub-narration-scheduler.timer",
                             "--property=ActiveState", "--value"))
    scheduler_enabled = run_command(("systemctl", "show", "epub-narration-scheduler.timer",
                                     "--property=UnitFileState", "--value"))
    monitor = run_command(("pct", "exec", "116", "--", "systemctl", "show",
                           "epub-narration-monitor.timer", "--property=ActiveState", "--value"))
    monitor_enabled = run_command(("pct", "exec", "116", "--", "systemctl", "show",
                                   "epub-narration-monitor.timer", "--property=UnitFileState", "--value"))
    worker_timer = run_command(("pct", "exec", "116", "--", "systemctl", "show",
                                "epub-narration-worker.timer", "--property=ActiveState", "--value"))
    worker_timer_enabled = run_command(("pct", "exec", "116", "--", "systemctl", "show",
                                        "epub-narration-worker.timer", "--property=UnitFileState", "--value"))
    worker_state = run_command(("pct", "exec", "116", "--", "systemctl", "show",
                                "epub-narration-worker.service",
                                "--property=ActiveState", "--value"))
    worker_result = run_command(("pct", "exec", "116", "--", "systemctl", "show",
                                 "epub-narration-worker.service",
                                 "--property=Result", "--value"))
    return (scheduler == "inactive" and scheduler_enabled == "disabled"
            and monitor == "active" and monitor_enabled == "enabled"
            and worker_timer == "inactive" and worker_timer_enabled == "disabled"
            and worker_state == "inactive" and worker_result == "success")'''
    return source[:start] + replacement + source[end:]


def session(source: str) -> str:
    consumers = '''FULL_DRAIN_CONSUMERS = (("104", "aster-agent.service"), ("116", "aster-speech.service"),
                        ("110", "aster-llama.service"),
                        ("114", "news-aggregator-ingest.timer"),
                        ("114", "news-aggregator-digest.timer"),
                        ("116", "epub-narration-worker.service"))'''
    consumers_new = '''FULL_DRAIN_CONSUMERS = (("104", "aster-agent.service"), ("116", "aster-speech.service"),
                        ("110", "aster-llama.service"),
                        ("114", "news-aggregator-ingest.timer"),
                        ("114", "news-aggregator-digest.timer"))'''
    source = once(source, consumers, consumers_new, "consumers")
    drain = '''    drain = tuple(_command(v, "systemctl", "mask", "--runtime", "--now", u)
                  for v, u in FULL_DRAIN_CONSUMERS[:-1]) + (
        _command("116", "systemctl", "stop", "epub-narration-worker.service"),
    )'''
    drain_new = '''    drain = tuple(_command(v, "systemctl", "mask", "--runtime", "--now", u)
                  for v, u in FULL_DRAIN_CONSUMERS)'''
    return once(source, drain, drain_new, "drain")


FIXTURE_OLD = '''            if command[-3:] == ("systemctl", "is-active", "epub-narration-worker.timer"): return 0, "active\\n"
            if command[-3:] == ("systemctl", "is-enabled", "epub-narration-worker.timer"): return 0, "enabled\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-worker.service", "--property=ActiveState", "--value"): return 0, "activating\\n"'''
FIXTURE_NEW = '''            if command == ("systemctl", "show", "epub-narration-scheduler.timer", "--property=ActiveState", "--value"): return 0, "inactive\\n"
            if command == ("systemctl", "show", "epub-narration-scheduler.timer", "--property=UnitFileState", "--value"): return 0, "disabled\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-monitor.timer", "--property=ActiveState", "--value"): return 0, "active\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-monitor.timer", "--property=UnitFileState", "--value"): return 0, "enabled\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-worker.timer", "--property=ActiveState", "--value"): return 0, "inactive\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-worker.timer", "--property=UnitFileState", "--value"): return 0, "disabled\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-worker.service", "--property=ActiveState", "--value"): return 0, "inactive\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-worker.service", "--property=Result", "--value"): return 0, "success\\n"'''


def build() -> dict[str, bytes]:
    output: dict[str, str] = {}
    output["full_inference_lab_sources.py"] = health(read("full_inference_lab_sources.py"))
    output["full_inference_lab_session.py"] = session(read("full_inference_lab_session.py"))
    preflight = read("full_inference_lab_install_preflight.py")
    preflight = once(preflight,
        "if len(drain) != 7 or len(FULL_DRAIN_CONSUMERS) != 7 or len(restore) != 14:",
        "if len(drain) != 5 or len(FULL_DRAIN_CONSUMERS) != 5 or len(restore) != 11:",
        "preflight-counts")
    output["full_inference_lab_install_preflight.py"] = preflight

    source_test = read("test_full_inference_lab_sources.py")
    output["test_full_inference_lab_sources.py"] = once(
        source_test, FIXTURE_OLD, FIXTURE_NEW, "source-fixture")
    validator_test = read("test_full_inference_lab_validator.py")
    validator_multiline = '''            if command[-3:] == ("systemctl", "is-active", "epub-narration-worker.timer"):
                return 0, "active\\n"
            if command[-3:] == ("systemctl", "is-enabled", "epub-narration-worker.timer"):
                return 0, "enabled\\n"
            if command[-5:] == ("systemctl", "show", "epub-narration-worker.service", "--property=ActiveState", "--value"):
                return 0, "activating\\n"'''
    validator_test = once(validator_test, validator_multiline, FIXTURE_NEW,
                          "validator-fixture-multiline")
    output["test_full_inference_lab_validator.py"] = once(
        validator_test, FIXTURE_OLD, FIXTURE_NEW, "validator-fixture-compact")

    install_test = read("test_full_inference_lab_install_preflight.py")
    install_test = once(install_test, 'self.assertEqual(value["drain_effects"], 7)',
                        'self.assertEqual(value["drain_effects"], 5)', "install-test-drain")
    install_test = once(install_test, 'self.assertEqual(value["restore_effects"], 14)',
                        'self.assertEqual(value["restore_effects"], 11)', "install-test-restore")
    output["test_full_inference_lab_install_preflight.py"] = install_test

    session_test = read("test_full_inference_lab_session.py")
    old_inventory = '''        self.assertIn("epub-narration-worker.timer", value.drain_commands[5])
        self.assertIn("epub-narration-worker.service", value.drain_commands[6])'''
    new_inventory = '''        self.assertFalse(any("epub-narration" in " ".join(command)
                             for command in value.drain_commands + value.restore_commands))'''
    session_test = once(session_test, old_inventory, new_inventory, "session-inventory")
    session_test = once(session_test, "self.assertEqual(len(calls), 7)",
                        "self.assertEqual(len(calls), len(value.drain_commands))", "session-drain-count")
    session_test = once(session_test, "self.assertEqual(len(calls), 21)",
                        "self.assertEqual(len(calls), len(value.drain_commands) + len(value.restore_commands))",
                        "session-total-count")
    session_test = once(session_test, "self.assertEqual(len(observations), 21)",
                        "self.assertEqual(len(observations), len(value.drain_commands) + len(value.restore_commands))",
                        "session-observation-count")
    session_test = once(session_test, "self.assertEqual(len(resumed_calls), 14)",
                        "self.assertEqual(len(resumed_calls), len(value.restore_commands))",
                        "session-resume-count")
    output["test_full_inference_lab_session.py"] = session_test

    supervisor_test = read("test_full_inference_lab_supervisor.py")
    supervisor_test = once(supervisor_test, "self.assertEqual(len(calls), 14)",
                           "self.assertEqual(len(calls), len(plan.restore_commands))", "supervisor-count")
    output["test_full_inference_lab_supervisor.py"] = supervisor_test

    observer_test = read("test_cooperative_lab_host_adapter.py")
    start = observer_test.index("    def test_observer_accepts_epub_static_unit")
    end = observer_test.index("\n\nif __name__", start)
    output["test_cooperative_lab_host_adapter.py"] = observer_test[:start] + observer_test[end:]

    manifest = json.loads(read("lab_hours_release_manifest.json"))
    for name, text in output.items():
        if name in manifest["pins"]:
            manifest["pins"][name] = sha(text.encode())
    result = {name: text.encode() for name, text in output.items()}
    result["lab_hours_release_manifest.json"] = (
        json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    return result


def atomic(path: Path, data: bytes) -> None:
    temporary = path.with_name("." + path.name + ".m5b-baseline")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def main() -> int:
    if os.geteuid() != 0 or os.uname().nodename != "proxmox":
        raise ReconcileError("PROXMOX_ROOT_REQUIRED")
    output = build()
    checkpoint = CHECKPOINTS / ("astertv-v3-m5b-retired-scheduler-" +
                                 time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    checkpoint.mkdir(mode=0o700, parents=True)
    for name in PINS:
        shutil.copy2(ROOT / name, checkpoint / name)
        (checkpoint / name).chmod(0o600)
    try:
        for name, data in output.items():
            atomic(ROOT / name, data)
        check = subprocess.run(
            ("/usr/bin/python3", "-B", "-m", "unittest", "discover", "-p", "test_*.py"),
            cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
        )
        if check.returncode != 0:
            raise ReconcileError("REGRESSION_TESTS_FAILED")
    except BaseException:
        for name in PINS:
            shutil.copy2(checkpoint / name, ROOT / name)
        raise
    print(json.dumps({"state": "reconciled", "tests": 71,
                      "checkpoint": str(checkpoint),
                      "scheduler_expected": "disabled-inactive",
                      "worker_expected": "inactive"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ReconcileError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"state": "no_go", "code": str(error)}, sort_keys=True))
        raise SystemExit(1)
