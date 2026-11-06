"""Mac-local host controls for the inert J2 CPU training transaction."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nlu_j2_artifact_contract_v1 as artifact_contract
import nlu_j2_training_transaction_v1 as transaction


TRANSACTION_SHA256 = "e9f8821b4316197b25cfac3c33a949128317002249da9f6b2cc4e0169e0435c8"
CORPUS_SHA256 = transaction.CORPUS_SHA256
RELEASE_SHA256 = transaction.CORPUS_RELEASE_SHA256
ADMISSION_SHA256 = "9994f4a2941503c5608ae85095bd0985d3292855c09bec0b6dfcb9e2aca00fd1"
RECIPE_SHA256 = transaction.artifact_contract.RECIPE_SHA256
LOCK_PATHS = (Path("/private/tmp/aster-mac-ai-exclusive.lock"),
              Path("/private/tmp/aster-j2-training.lock"))
COMPETING_PROCESS_PATTERNS = (
    "nlu_j2_training_transaction_v1.py",
    "nlu_j1_training_execute_v1.py",
    "mlx_lm.generate", "mlx_lm.server",
)
MIN_AVAILABLE_BYTES = 2 * 1024 ** 3
MAX_SWAP_GROWTH_BYTES = 256 * 1024 ** 2
MAX_RUNTIME_SECONDS = 7200
POLL_SECONDS = 5


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bytes(value: str) -> int:
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMG])", value)
    if not match:
        raise ValueError("Mac swap observation changed")
    scale = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}[match.group(2)]
    return round(float(match.group(1)) * scale)


def resources() -> dict[str, int]:
    vm = subprocess.run(["/usr/bin/vm_stat"], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, check=False, text=True)
    swap = subprocess.run(["/usr/sbin/sysctl", "-n", "vm.swapusage"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False, text=True)
    if vm.returncode or vm.stderr or swap.returncode or swap.stderr:
        raise RuntimeError("Mac resource observation failed")
    page_match = re.search(r"page size of ([0-9]+) bytes", vm.stdout)
    values = {name: int(count.replace(".", ""))
              for name, count in re.findall(r"Pages (free|inactive|speculative):\s+([0-9.]+)", vm.stdout)}
    swap_match = re.search(r"used = ([0-9]+(?:\.[0-9]+)?[KMG])", swap.stdout)
    if not page_match or set(values) != {"free", "inactive", "speculative"} or not swap_match:
        raise ValueError("Mac resource observation shape changed")
    return {"available_bytes": sum(values.values()) * int(page_match.group(1)),
            "swap_used_bytes": _bytes(swap_match.group(1))}


def competing_processes() -> list[int]:
    completed = subprocess.run(["/bin/ps", "-axo", "pid=,command="],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False, text=True)
    if completed.returncode or completed.stderr:
        raise RuntimeError("Mac process admission observation failed")
    current = os.getpid()
    matches = []
    for line in completed.stdout.splitlines():
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2 or not fields[0].isdigit():
            continue
        pid, command = int(fields[0]), fields[1]
        if pid != current and any(pattern in command
                                  for pattern in COMPETING_PROCESS_PATTERNS):
            matches.append(pid)
    return sorted(set(matches))


def validate_inputs(corpus: Path, release: Path, admission: Path,
                    recipe: Path) -> None:
    expected = ((corpus, CORPUS_SHA256), (release, RELEASE_SHA256),
                (admission, ADMISSION_SHA256), (recipe, RECIPE_SHA256),
                (Path(transaction.__file__), TRANSACTION_SHA256))
    if any(not path.is_file() or path.is_symlink() or _sha256(path) != digest
           for path, digest in expected):
        raise ValueError("J2 Mac owner input or workload pin changed")


def _lock(path: Path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    handle = os.fdopen(descriptor, "r+")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return handle


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


def run(corpus: Path, release: Path, admission: Path, recipe: Path,
        output: Path) -> dict[str, object]:
    if output.exists():
        raise ValueError("J2 Mac retained output directory already exists")
    validate_inputs(corpus, release, admission, recipe)
    locks = []
    process = None
    initial = resources()
    if initial["available_bytes"] < MIN_AVAILABLE_BYTES:
        raise RuntimeError("J2 Mac memory admission failed")
    if competing_processes():
        raise RuntimeError("J2 Mac process admission failed")
    try:
        locks = [_lock(path) for path in LOCK_PATHS]
        # Recheck after locking so the observation-to-effect boundary is closed.
        validate_inputs(corpus, release, admission, recipe)
        locked_resources = resources()
        if (locked_resources["available_bytes"] < MIN_AVAILABLE_BYTES
                or locked_resources["swap_used_bytes"]
                != initial["swap_used_bytes"]
                or competing_processes()):
            raise RuntimeError("J2 Mac host admission changed after lock")
        command = [
            sys.executable, "-I", "-B", str(Path(transaction.__file__).resolve()),
            "--corpus", str(corpus.resolve()), "--release", str(release.resolve()),
            "--admission", str(admission.resolve()), "--recipe", str(recipe.resolve()),
            "--output", str(output.resolve()),
        ]
        environment = transaction._clean_environment()
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=environment, start_new_session=True)
        deadline = time.monotonic() + MAX_RUNTIME_SECONDS
        observations = 0
        minimum_available = initial["available_bytes"]
        maximum_swap = initial["swap_used_bytes"]
        while process.poll() is None:
            if time.monotonic() >= deadline:
                raise TimeoutError("J2 Mac bounded runtime exceeded")
            current = resources(); observations += 1
            minimum_available = min(minimum_available, current["available_bytes"])
            maximum_swap = max(maximum_swap, current["swap_used_bytes"])
            if (current["available_bytes"] < MIN_AVAILABLE_BYTES
                    or current["swap_used_bytes"] - initial["swap_used_bytes"]
                    > MAX_SWAP_GROWTH_BYTES):
                raise RuntimeError("J2 Mac resource supervision gate failed")
            time.sleep(POLL_SECONDS)
        stdout, stderr = process.communicate(timeout=10)
        if process.returncode or stderr:
            raise RuntimeError("J2 Mac training owner failed closed")
        summary = json.loads(stdout)
        if (summary.get("status") != "complete"
                or summary.get("authority") != "none"
                or summary.get("automatic_routing") != "off"
                or summary.get("deployment") is not False
                or set(path.name for path in output.iterdir())
                != set(transaction.OUTPUT_NAMES)):
            raise RuntimeError("J2 Mac completion postcheck failed")
        if process.poll() != 0:
            raise RuntimeError("J2 Mac process restoration failed")
        return {"schema": "aster-nlu-j2-mac-host-result.v1",
                "status": "complete", "resource_observations": observations,
                "minimum_available_bytes": minimum_available,
                "maximum_swap_used_bytes": maximum_swap,
                "services_stopped": 0, "production_changed": False,
                "b60_used": False, "b60_booking_required": False,
                "authority": "none", "automatic_routing": "off",
                "deployment": False}
    except BaseException:
        if process is not None:
            _terminate(process)
        raise
    finally:
        for handle in reversed(locks):
            handle.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--admission", required=True, type=Path)
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.corpus, args.release, args.admission, args.recipe, args.output)
    print(artifact_contract.canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
