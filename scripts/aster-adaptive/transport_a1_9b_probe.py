"""Send a frozen synthetic probe to LXC 110 without copying its API key.

This script performs model calls. Run only after the dated card's live gate.
Raw synthetic answers are written mode 0600 outside Git, never to stdout.
"""
import argparse
import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path

from a1_9b_synthetic_answer_probe import FIXTURE_SHA256, PROFILE_SHA256, SYSTEM

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "answer-feasibility-v0.json"
PROBE = HERE / "a1_9b_synthetic_answer_probe.py"
PROFILE = HERE.parents[1] / "docs/projects/AI Projects/benchmarks/a1-9b-synthetic-profile-v0.json"
REMOTE = ["ssh", "-o", "BatchMode=yes", "root@proxmox",
          "pct exec 110 -- runuser -u ollama -- python3 -"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output already exists; uncertain requests are never retried")
    profile_raw = PROFILE.read_bytes()
    profile = json.loads(profile_raw)
    if (hashlib.sha256(profile_raw).hexdigest() != PROFILE_SHA256
            or hashlib.sha256(FIXTURE.read_bytes()).hexdigest() != FIXTURE_SHA256
            or profile.get("system_prompt_sha256") != hashlib.sha256(SYSTEM.encode()).hexdigest()
            or profile.get("tool_mode") != "disabled"):
        raise SystemExit("frozen profile/fixture/prompt mismatch; no model call")
    injected = "FROZEN_FIXTURE_B64 = " + repr(base64.b64encode(FIXTURE.read_bytes()).decode()) + "\n"
    result = subprocess.run(REMOTE, input=injected + PROBE.read_text(),
                            text=True, capture_output=True, timeout=650, check=False)
    if result.returncode != 0:
        raise SystemExit("probe transport failed; no automatic retry (exit %d)" % result.returncode)
    try:
        packet = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise SystemExit("probe returned invalid envelope; no automatic retry")
    if (packet.get("schema_version") != "aster-answer-capture.v0"
            or packet.get("tool_mode") != "disabled"
            or not isinstance(packet.get("attempts"), list)
            or len(packet["attempts"]) > 6):
        raise SystemExit("probe returned unexpected scope; no automatic retry")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(packet, handle, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"path": str(args.output), "attempted": len(packet["attempts"]),
                      "terminal_failures": sum(row.get("status") == "failed"
                                               for row in packet["attempts"]),
                      "raw_answers": "stored locally; do not commit"}, sort_keys=True))


if __name__ == "__main__":
    main()
