#!/usr/bin/env python3
"""Create the bounded health summary that Aster may read.

The report intentionally contains only Doctor's pass/warn/fail lines and its
aggregate outcome.  It never publishes raw command output, environment values,
credentials, or a way for Aster to execute Doctor itself.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


LINE = re.compile(r"^([🟢🟡🔴])\s+(.+)$")
STATUS = {"🟢": "pass", "🟡": "warn", "🔴": "fail"}
STRUCTURED_CHECK_ID = "aster.agent_inference"
MAX_STRUCTURED_BYTES = 4096


def _atomic_write(path: Path, payload: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temporary:
            temporary.write(payload)
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate structured event field")
        result[key] = value
    return result


def _structured_state(raw: bytes, run_id: str) -> str:
    """Accept one exact, same-invocation producer event or abstain."""
    if len(raw) > MAX_STRUCTURED_BYTES:
        return "unavailable"
    try:
        lines = raw.decode("utf-8").splitlines()
        if len(lines) != 1:
            return "unavailable"
        event = json.loads(lines[0], object_pairs_hook=_unique_object)
        if not isinstance(event, dict) or set(event) != {"run_id", "check_id", "state"}:
            return "unavailable"
        if event["run_id"] != run_id or event["check_id"] != STRUCTURED_CHECK_ID:
            return "unavailable"
        if event["state"] not in {"pass", "warn", "fail", "unavailable"}:
            return "unavailable"
        return event["state"]
    except (UnicodeError, ValueError, TypeError):
        return "unavailable"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Aster's sanitized Doctor summary")
    parser.add_argument("--output", type=Path, required=True, help="root-owned destination JSON file")
    parser.add_argument("--doctor", type=Path, default=Path(__file__).with_name("doctor.sh"))
    parser.add_argument("--input", type=Path, help="Reuse a captured Doctor output file instead of running Doctor")
    parser.add_argument("--exit-code", type=int, default=0, help="Exit code of the captured Doctor run")
    parser.add_argument("--publish", action="store_true", help="Publish to the existing Aster health path via Proxmox")
    parser.add_argument("--structured-output", type=Path, help="Local schema-2 fixed-check sidecar")
    parser.add_argument("--capture-output", type=Path, help="Private transcript from the fresh Doctor run")
    parser.add_argument("--result-output", type=Path, help="Content-free collector result for the scheduler")
    args = parser.parse_args()

    if args.input and (args.structured_output or args.capture_output):
        parser.error("structured or captured output requires one fresh Doctor run")
    destinations = [path.resolve() for path in (
        args.output, args.structured_output, args.capture_output, args.result_output,
    ) if path]
    if len(destinations) != len(set(destinations)):
        parser.error("output, structured output and capture output must be separate files")

    run_id = uuid.uuid4().hex if args.structured_output else ""
    structured_raw = b""

    if args.input:
        completed = subprocess.CompletedProcess([], args.exit_code, args.input.read_text(), "")
    else:
        try:
            if args.structured_output:
                with tempfile.TemporaryFile(mode="w+b") as evidence:
                    environment = os.environ.copy()
                    environment["DOCTOR_STRUCTURED_FD"] = str(evidence.fileno())
                    environment["DOCTOR_RUN_ID"] = run_id
                    completed = subprocess.run(
                        [str(args.doctor)], text=True, capture_output=True, check=False,
                        timeout=900, env=environment, pass_fds=(evidence.fileno(),),
                    )
                    evidence.seek(0)
                    structured_raw = evidence.read(MAX_STRUCTURED_BYTES + 1)
            else:
                environment = os.environ.copy()
                environment.pop("DOCTOR_STRUCTURED_FD", None)
                environment.pop("DOCTOR_RUN_ID", None)
                completed = subprocess.run(
                    [str(args.doctor)], text=True, capture_output=True, check=False,
                    timeout=900, env=environment,
                )
        except subprocess.TimeoutExpired:
            completed = subprocess.CompletedProcess([], 1, "🔴 Doctor timed out; health collection is incomplete.", "")
    if args.capture_output:
        capture_payload = completed.stdout + ("\n" if completed.stdout and completed.stderr else "") + completed.stderr
        if capture_payload and not capture_payload.endswith("\n"):
            capture_payload += "\n"
        _atomic_write(args.capture_output, capture_payload)
    checks: list[dict[str, str]] = []
    for line in (completed.stdout + "\n" + completed.stderr).splitlines():
        match = LINE.match(line)
        if match:
            checks.append({"name": "HomeLab Doctor", "status": STATUS[match.group(1)], "summary": match.group(2)[:500]})
    if not checks:
        checks.append({"name": "HomeLab Doctor", "status": "fail", "summary": "Doctor produced no recognizable checks; health collection is incomplete."})
    overall = "failed" if completed.returncode or any(c["status"] == "fail" for c in checks) else ("warning" if any(c["status"] == "warn" for c in checks) else "healthy")
    # Preserve actionable states if Doctor grows beyond the report-size cap.
    selected_checks = [check for check in checks if check["status"] != "pass"]
    selected_checks.extend(check for check in checks if check["status"] == "pass")
    if completed.returncode and not selected_checks:
        selected_checks.append({"name": "HomeLab Doctor", "status": "fail", "summary": "Doctor exited unsuccessfully; use the operator report for details."})
    report = {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": overall,
        "checks": selected_checks[:32],
    }
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    _atomic_write(args.output, payload)
    structured_payload = ""
    if args.structured_output:
        candidate = {
            "schema": 2,
            "generated_at": report["generated_at"],
            "run_id": run_id,
            "source_report_digest": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "checks": [{"check_id": STRUCTURED_CHECK_ID, "state": _structured_state(structured_raw, run_id)}],
        }
        structured_payload = json.dumps(candidate, sort_keys=True, separators=(",", ":")) + "\n"
        _atomic_write(args.structured_output, structured_payload)
    if args.publish:
        # Fixed destinations and commands; an encoded envelope goes over stdin,
        # never shell interpolation. The sidecar is written last. A reader that
        # races either replace sees a digest mismatch and safely abstains.
        writer = """import base64,grp,hashlib,json,os,pathlib,sys
envelope=json.load(sys.stdin)
assert set(envelope)=={'aggregate','structured'}
aggregate=base64.b64decode(envelope['aggregate'],validate=True)
value=json.loads(aggregate)
assert value['schema']==1 and value['status'] in ('healthy','warning','failed')
assert isinstance(value['checks'],list) and len(value['checks'])<=32
root=pathlib.Path('/var/lib/aster/health'); root.mkdir(exist_ok=True)
target=root/'latest.json'; temp=root/'latest.json.new'
temp.write_bytes(aggregate)
os.chmod(temp,0o640); os.chown(temp,0,grp.getgrnam('aster').gr_gid)
os.replace(temp,target)
if envelope['structured'] is not None:
    structured=base64.b64decode(envelope['structured'],validate=True)
    sidecar=json.loads(structured)
    assert set(sidecar)=={'schema','generated_at','run_id','source_report_digest','checks'}
    assert sidecar['schema']==2 and sidecar['generated_at']==value['generated_at']
    assert sidecar['source_report_digest']==hashlib.sha256(aggregate).hexdigest()
    assert isinstance(sidecar['run_id'],str) and len(sidecar['run_id'])==32
    assert isinstance(sidecar['checks'],list) and len(sidecar['checks'])==1
    check=sidecar['checks'][0]
    assert set(check)=={'check_id','state'} and check['check_id']=='aster.agent_inference'
    assert check['state'] in ('pass','warn','fail','unavailable')
    side_target=root/'aster-inference.json'; side_temp=root/'aster-inference.json.new'
    side_temp.write_bytes(structured)
    os.chmod(side_temp,0o640); os.chown(side_temp,0,grp.getgrnam('aster').gr_gid)
    os.replace(side_temp,side_target)
"""
        remote = "pct exec 104 -- python3 -c " + shlex.quote(writer)
        envelope = json.dumps({
            "aggregate": base64.b64encode(payload.encode("utf-8")).decode("ascii"),
            "structured": (base64.b64encode(structured_payload.encode("utf-8")).decode("ascii")
                           if structured_payload else None),
        }, separators=(",", ":"))
        subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        "root@192.168.50.10", remote], input=envelope, text=True, check=True, timeout=30)
    if args.result_output:
        result_payload = json.dumps({"doctor_exit": completed.returncode}, separators=(",", ":")) + "\n"
        _atomic_write(args.result_output, result_payload)
        return 0
    return 0 if args.input else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
