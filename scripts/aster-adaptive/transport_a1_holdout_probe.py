"""One-shot transport for the sealed fictional Aster 20-case development run.

This makes model calls only when main() executes. The API key stays inside LXC
110. Do not invoke before the dated run card's live lease/profile/backup gate.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from a1_9b_synthetic_answer_probe import SYSTEM
from holdout_answer_capture import CASE_SHA256, reserve_private


HERE = Path(__file__).resolve().parent
PROFILE = HERE.parents[1] / "docs/projects/AI Projects/benchmarks/a1-answer-holdout-9b-profile-v1.json"
PROFILE_SHA256 = "712b0d469e4e35cc3bf2a1cb324014a3390aa1e04b06b1832fbcbf4d0474a349"
CASES = Path.home() / "Library/Application Support/Aster-Stream-A-Evidence/answer-holdout-20261012-v1/cases.jsonl"
SOURCES = {name: HERE / (name + ".py") for name in
           ("a1_9b_synthetic_answer_probe", "holdout_answer_capture",
            "holdout_answer_9b_adapter")}
REMOTE = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
          "root@proxmox", "pct exec 110 -- runuser -u ollama -- python3 -"]


def validate_profile(profile_raw: bytes, cases_raw: bytes) -> dict:
    if hashlib.sha256(profile_raw).hexdigest() != PROFILE_SHA256:
        raise ValueError("frozen profile digest mismatch")
    profile = json.loads(profile_raw)
    if (hashlib.sha256(cases_raw).hexdigest() != CASE_SHA256
            or profile.get("case_fixture_sha256") != CASE_SHA256
            or profile.get("system_prompt_sha256") != hashlib.sha256(SYSTEM.encode()).hexdigest()
            or profile.get("model_id") != "aster-qwen3.5-9b"
            or profile.get("tool_mode") != "disabled"
            or profile.get("egress") != "local"
            or profile.get("per_request_timeout_seconds") != 60
            or profile.get("batch_max_wall_seconds") != 600):
        raise ValueError("frozen run scope mismatch")
    return profile


def remote_program(cases_raw: bytes, source_raw: dict[str, bytes]) -> str:
    encoded = {name: base64.b64encode(raw).decode("ascii") for name, raw in source_raw.items()}
    return "\n".join([
        "import base64,json,sys,types",
        "from pathlib import Path",
        "modules = " + repr(encoded),
        "for name in ('a1_9b_synthetic_answer_probe','holdout_answer_capture','holdout_answer_9b_adapter'):",
        "    mod=types.ModuleType(name)",
        "    mod.__file__='/tmp/aster-holdout/'+name+'.py'",
        "    sys.modules[name]=mod",
        "    exec(compile(base64.b64decode(modules[name]),mod.__file__,'exec'),mod.__dict__)",
        "cases_raw=base64.b64decode(" + repr(base64.b64encode(cases_raw).decode("ascii")) + ",validate=True)",
        "from a1_9b_synthetic_answer_probe import KEY_PATH",
        "from holdout_answer_9b_adapter import invoke",
        "from holdout_answer_capture import capture",
        "key=KEY_PATH.read_text().splitlines()[0].strip()",
        "if not key: raise SystemExit('source-local service credential unavailable')",
        "result=capture(cases_raw," + repr(PROFILE_SHA256) + ",lambda case: invoke(case,key),max_wall_s=600)",
        "print(json.dumps(result,sort_keys=True))",
        "",
    ])


def seal_stdout(directory: Path, stdout: str) -> tuple[Path, str]:
    """Seal raw transport output before parsing; use owner-only fallback on error."""
    raw = stdout.encode("utf-8")
    def write(target: Path) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(target / "raw-attempts.json", flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    try:
        write(directory)
        actual = directory
    except OSError:
        actual = Path(tempfile.mkdtemp(prefix="aster-holdout-recovery-", dir="/private/tmp"))
        write(actual)
    return actual, hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit("output already exists; uncertain requests are never retried")
    cases_raw = CASES.read_bytes()
    validate_profile(PROFILE.read_bytes(), cases_raw)
    sources = {name: path.read_bytes() for name, path in SOURCES.items()}
    program = remote_program(cases_raw, sources)
    reserve_private(args.output_dir)
    try:
        result = subprocess.run(REMOTE, input=program, text=True,
                                capture_output=True, timeout=660, check=False)
    except subprocess.TimeoutExpired as error:
        partial = error.stdout or b""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        actual_dir, _ = seal_stdout(args.output_dir, partial)
        raise SystemExit("probe timed out; partial output sealed privately at %s; no retry" % actual_dir)
    actual_dir, raw_digest = seal_stdout(args.output_dir, result.stdout)
    if result.returncode:
        raise SystemExit("probe transport failed; raw output sealed privately at %s; no retry (exit %d)" % (actual_dir, result.returncode))
    try:
        packet = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise SystemExit("probe returned invalid envelope; raw output sealed privately at %s; no retry" % actual_dir)
    if (packet.get("schema_version") != "aster-answer-holdout-capture.v1"
            or packet.get("cases_sha256") != CASE_SHA256
            or packet.get("profile_sha256") != PROFILE_SHA256
            or packet.get("tool_mode") != "disabled"
            or not isinstance(packet.get("attempts"), list)
            or len(packet["attempts"]) != 20):
        raise SystemExit("probe returned unexpected scope; raw output sealed privately at %s; no retry" % actual_dir)
    summary = {"planned": len(packet["attempts"]),
               "completed": sum(row.get("status") == "completed" for row in packet["attempts"]),
               "failed": sum(row.get("status") == "failed" for row in packet["attempts"]),
               "not_attempted": sum(row.get("status") == "not_attempted" for row in packet["attempts"])}
    print(json.dumps({"output_dir": str(actual_dir), "raw_attempts_sha256": raw_digest,
                      **summary,
                      "profile_sha256": PROFILE_SHA256}, sort_keys=True))


if __name__ == "__main__":
    main()
