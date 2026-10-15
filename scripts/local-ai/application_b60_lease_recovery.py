"""Fixed host-local recovery CLI for the application-only B60 lease."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from a1_ingress_policy import baseline, parse_chain
from application_b60_watchdog import ApplicationB60Watchdog, fixed_command

RECEIPT = Path("/var/lib/local-ai-lab/application-b60/recovery-receipt.json")
SOURCE_HASHES = {
    "/opt/aster-a1-test/a1_isolated_app.py": "b634b0518f018befc88f57697b55ad1ef1011fc107c1088bd90158656c53fed4",
    "/opt/aster-a1-test/a1_test_gateway.py": "e2e1150a76fd6e61c47da1a6c6f3ce229905a454476c756c49d6a83c9d10aaae",
    "/opt/aster-a1-test/aster-agent/aster_agent.py": "d6a05bcc7edddb1eaa69a67450cfc48c1c0e96ba8688de7a1246a1e9eb847e11",
}


def _run(argv: Sequence[str], timeout: float = 10.0) -> tuple[int, str]:
    result = subprocess.run(tuple(argv), capture_output=True, text=True, timeout=timeout, check=False)
    return result.returncode, result.stdout.strip()


def _pct(vmid: str, *command: str) -> tuple[str, ...]:
    return ("pct", "exec", vmid, "--", *command)


class HostObserver:
    def sidecar_stopped(self) -> bool:
        code, output = _run(_pct("104", "systemctl", "is-active", "aster-a1-test.service"))
        return code != 0 and output == "inactive"

    def ingress_restored(self) -> bool:
        code, output = _run(_pct("110", "nft", "-j", "-s", "list", "chain", "inet", "filter", "input"))
        if code != 0:
            return False
        try:
            chain, rules = parse_chain(output)
            return baseline(chain, rules)
        except (ValueError, json.JSONDecodeError):
            return False

    def test_key_removed(self) -> bool:
        code, output = _run(_pct("110", "/usr/local/sbin/aster-llama-test-key-status"))
        return code == 0 and output == "removed"

    def backend_reloaded(self) -> bool:
        code, output = _run(_pct("110", "systemctl", "is-active", "aster-llama.service"))
        return code == 0 and output == "active"

    def production_auth_ok(self) -> bool:
        code, _ = _run(_pct("110", "/usr/local/sbin/aster-llama-production-auth-probe"), timeout=15.0)
        return code == 0

    def wrong_key_denied(self) -> bool:
        command = ("curl", "-sS", "--max-time", "5", "-o", "/dev/null", "-w", "%{http_code}", "-H", "Authorization: Bearer a1-invalid-key", "-H", "Content-Type: application/json", "--data", "{\"model\":\"aster-qwen3.5-9b\",\"messages\":[{\"role\":\"user\",\"content\":\"health\"}],\"max_tokens\":1}", "http://192.168.70.12:11435/v1/chat/completions")
        code, output = _run(_pct("110", *command), timeout=10.0)
        return code == 0 and output == "401"

    def aster_healthy(self) -> bool:
        code, output = _run(_pct("104", "systemctl", "is-active", "aster-agent.service"))
        return code == 0 and output == "active"

    def speech_healthy(self) -> bool:
        code, output = _run(_pct("116", "systemctl", "is-active", "aster-speech.service"))
        return code == 0 and output == "active"

    def consumers_healthy(self) -> bool:
        return self.aster_healthy() and self.speech_healthy()

    def source_checks(self) -> bool:
        for path, expected in SOURCE_HASHES.items():
            code, output = _run(_pct("104", "sha256sum", path))
            if code != 0 or output.split()[:1] != [expected]:
                return False
        return True


def _write_receipt(payload: dict[str, object]) -> None:
    RECEIPT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd, name = tempfile.mkstemp(prefix=".recovery-receipt.", dir=RECEIPT.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, RECEIPT)
        directory = os.open(RECEIPT.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Application-only B60 lease recovery")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.once:
        raise SystemExit("--once is required")
    state = json.loads(args.state.read_text(encoding="utf-8"))
    for key in ("mode", "lease_id", "generation", "armed", "start_deadline_epoch", "restore_deadline_epoch"):
        if key not in state:
            raise SystemExit("application state schema is incomplete")
    if args.dry_run:
        print(json.dumps({"state": "dry-run", "mode": state["mode"], "lease_id": state["lease_id"], "generation": state["generation"], "armed": state["armed"], "commands": [list(fixed_command(name)) for name in ("stop-sidecar", "restore-ingress", "remove-test-key", "reload-backend", "start-aster", "start-speech")]}, sort_keys=True, separators=(",", ":")))
        return 0
    if os.geteuid() != 0:
        raise SystemExit("application recovery must run as root")
    if not args.effect_authorized:
        raise SystemExit("effect authority is required")
    observer = HostObserver()
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    if now_epoch < state["restore_deadline_epoch"]:
        print(json.dumps({"state": "waiting", "lease_id": state["lease_id"], "generation": state["generation"], "now_epoch": now_epoch, "restore_deadline_epoch": state["restore_deadline_epoch"]}, sort_keys=True, separators=(",", ":")))
        return 0
    source_ok = observer.source_checks()
    watchdog = ApplicationB60Watchdog(args.state.parent, lambda command: _run(command, timeout=30.0)[0] == 0 or (_ for _ in ()).throw(RuntimeError("fixed recovery command failed")), observer, allow_effects=True)
    result = watchdog.recover(lease_id=state["lease_id"], generation=state["generation"], now_epoch=now_epoch, retain_state=True)
    _write_receipt({"schema": "aster-application-recovery.v1", "state": result["state"], "mode": result["mode"], "lease_id": result["lease_id"], "generation": result["generation"], "overdue": result["overdue"], "source_checks": "candidate-closure-verified" if source_ok else "candidate-closure-drift-observed"})
    watchdog.finalize(lease_id=result["lease_id"], generation=result["generation"])
    print(json.dumps({"state": "recovery-receipt-written", "lease_id": result["lease_id"], "generation": result["generation"], "overdue": result["overdue"]}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
