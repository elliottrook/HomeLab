#!/usr/bin/env python3
"""Guest-local, content-minimizing D4/M3 outcome verifier.

Private artifact bytes are opened and verified inside their owning guest.  The
only successful output is a canonical content-free digest/count projection.
This source is not installed or callable from the host until a later reviewed
packet supplies the fixed wrapper.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pwd
import stat

from stream_a_evaluation_outcome_verifier import (
    MAX_D4_LEDGER_BYTES,
    MAX_M3_JOURNAL_BYTES,
    MAX_M3_RUN_BYTES,
    verify_d4_ledger,
    verify_m3_artifacts,
)


class GuestOutcomeError(ValueError):
    pass


D4_ROOT = Path("/var/lib/aster/d4-candidate-h-output")
M3_ROOT = Path("/var/lib/aster-nlu-calibration/nlu-calibration-v1")
SCHEMA = "stream-a-evaluation-content-free-outcome-v1"
M3_UID = 0


def _read(path: Path, *, parent_uid: int, file_uid: int, maximum: int) -> bytes:
    parent = path.parent.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != parent_uid
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise GuestOutcomeError("artifact parent custody is invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise GuestOutcomeError("artifact cannot be opened safely") from error
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != file_uid
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                or not 0 < info.st_size <= maximum):
            raise GuestOutcomeError("artifact custody or size is invalid")
        raw = os.read(descriptor, maximum + 1)
        if len(raw) != info.st_size:
            raise GuestOutcomeError("artifact changed while being read")
        return raw
    finally:
        os.close(descriptor)


def verify_local(name: str) -> dict[str, object]:
    if name == "d4-candidate-h":
        try:
            uid = pwd.getpwnam("aster-d4-eval").pw_uid
        except KeyError as error:
            raise GuestOutcomeError("fixed D4 identity is absent") from error
        evidence = verify_d4_ledger(_read(
            D4_ROOT / "attempt-journal.jsonl", parent_uid=uid,
            file_uid=uid, maximum=MAX_D4_LEDGER_BYTES,
        ))
    elif name == "m3-nlu-calibration":
        run = _read(M3_ROOT / "run.json", parent_uid=M3_UID, file_uid=M3_UID,
                    maximum=MAX_M3_RUN_BYTES)
        journal = _read(M3_ROOT / "attempt-journal.jsonl", parent_uid=M3_UID,
                        file_uid=M3_UID, maximum=MAX_M3_JOURNAL_BYTES)
        evidence = verify_m3_artifacts(run, journal)
    else:
        raise GuestOutcomeError("workload is not fixed")
    return {
        "schema": SCHEMA, "name": name,
        "journal_digest": evidence.journal_digest,
        "result_digest": evidence.result_digest,
        "calls": evidence.calls,
    }


def canonical(value: dict[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload",
                        choices=("d4-candidate-h", "m3-nlu-calibration"))
    parser.add_argument("--verify-authorized", action="store_true")
    arguments = parser.parse_args(argv)
    if not arguments.verify_authorized:
        print(canonical({"schema": SCHEMA, "state": "disabled"}), end="")
        return 0
    if arguments.workload is None:
        print(canonical({"schema": SCHEMA, "state": "no_go"}), end="")
        return 1
    try:
        value = verify_local(arguments.workload)
    except (GuestOutcomeError, OSError, ValueError):
        print(canonical({"schema": SCHEMA, "state": "no_go"}), end="")
        return 1
    print(canonical(value), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
