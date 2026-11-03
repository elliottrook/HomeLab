"""Execute the approved J1 training transaction with two clean reproductions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nlu_j1_training_recipe_v1 as recipe


SCHEMA = "aster-nlu-j1-training-execution.v1"
RECEIPT_NAMES = tuple([f"calibration-v{i}" for i in range(1, 7)] + ["development-v1"])
FORBIDDEN_AUDIT_PREFIXES = ("socket.", "ssl.")


def _audit(event: str, _args: tuple[object, ...]) -> None:
    if event.startswith(FORBIDDEN_AUDIT_PREFIXES):
        raise RuntimeError("network access is forbidden during J1 training")


def _write_exclusive(path: Path, raw: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def _inputs(corpus: Path, release: Path, private_dir: Path) -> tuple[bytes, bytes, bytes, dict[str, bytes]]:
    corpus_raw = corpus.read_bytes()
    release_raw = release.read_bytes()
    result_raw = (private_dir / "private-review-result.json").read_bytes()
    receipts = {name: (private_dir / f"{name}.json").read_bytes() for name in RECEIPT_NAMES}
    return corpus_raw, release_raw, result_raw, receipts


def worker(corpus: Path, release: Path, private_dir: Path, output_dir: Path) -> None:
    """Run one isolated reproduction and write only content-free model evidence."""
    if not output_dir.is_dir() or any(output_dir.iterdir()):
        raise ValueError("worker output directory must exist and be empty")
    sys.addaudithook(_audit)
    corpus_raw, release_raw, result_raw, receipts = _inputs(corpus, release, private_dir)
    artifact, summary = recipe.train_exact(corpus_raw, receipts, result_raw, release_raw)
    _write_exclusive(output_dir / "artifact.json", recipe.canonical(artifact))
    _write_exclusive(output_dir / "summary.json", recipe.canonical(summary))


def execute(corpus: Path, release: Path, private_dir: Path, output_dir: Path) -> dict[str, object]:
    """Require two byte-identical clean workers, then retain one exact artifact."""
    if output_dir.exists():
        raise ValueError("retained output directory already exists")
    output_dir.mkdir(mode=0o700, parents=False)
    script = Path(__file__).resolve()
    outputs = []
    try:
        for number in (1, 2):
            with tempfile.TemporaryDirectory(prefix=f"aster-j1-run-{number}-") as temporary:
                destination = Path(temporary)
                environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                               "PYTHONHASHSEED": "0", "LC_ALL": "C", "LANG": "C"}
                command = [sys.executable, "-I", "-B", str(script), "--worker",
                           "--corpus", str(corpus.resolve()), "--release", str(release.resolve()),
                           "--private-dir", str(private_dir.resolve()), "--output", str(destination)]
                completed = subprocess.run(command, cwd=temporary, env=environment,
                                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, timeout=60, check=False)
                if completed.returncode or completed.stdout or completed.stderr:
                    raise RuntimeError(f"clean reproduction {number} failed closed")
                outputs.append(((destination / "artifact.json").read_bytes(),
                                (destination / "summary.json").read_bytes()))
        if outputs[0] != outputs[1]:
            raise RuntimeError("clean reproductions differ")
        artifact_raw, summary_raw = outputs[0]
        artifact = json.loads(artifact_raw)
        summary = json.loads(summary_raw)
        corpus_raw, release_raw, result_raw, receipts = _inputs(corpus, release, private_dir)
        receipt = {"schema": SCHEMA, "status": "complete", "reproductions": 2,
                   "reproductions_identical": True,
                   "executor_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                   "corpus_sha256": hashlib.sha256(corpus_raw).hexdigest(),
                   "release_candidate_sha256": hashlib.sha256(release_raw).hexdigest(),
                   "private_result_sha256": hashlib.sha256(result_raw).hexdigest(),
                   "receipt_set_sha256": hashlib.sha256(recipe.canonical({
                       name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(receipts.items())
                   })).hexdigest(),
                   "artifact_sha256": artifact["artifact_sha256"],
                   "artifact_file_sha256": hashlib.sha256(artifact_raw).hexdigest(),
                   "summary_file_sha256": hashlib.sha256(summary_raw).hexdigest(),
                   "validation_exact": summary["validation_exact"],
                   "guarded_validation_exact": summary["guarded_validation_exact"],
                   "accepted_validation": summary["accepted_validation"],
                   "accepted_validation_exact": summary["accepted_validation_exact"],
                   "margin_threshold": summary["margin_threshold"],
                   "authority": "not-granted", "automatic_routing": "off",
                   "public_gate_opened": False, "sealed_holdout_read": False,
                   "network": "forbidden"}
        _write_exclusive(output_dir / "artifact.json", artifact_raw)
        _write_exclusive(output_dir / "summary.json", summary_raw)
        _write_exclusive(output_dir / "execution-receipt.json", recipe.canonical(receipt))
        return receipt
    except BaseException:
        for path in output_dir.glob("*"):
            path.unlink()
        output_dir.rmdir()
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--private-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.corpus, args.release, args.private_dir, args.output)
        return 0
    receipt = execute(args.corpus, args.release, args.private_dir, args.output)
    print(json.dumps({"status": receipt["status"], "reproductions": receipt["reproductions"],
                      "artifact_sha256": receipt["artifact_sha256"],
                      "authority": receipt["authority"],
                      "automatic_routing": receipt["automatic_routing"]},
                     sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
