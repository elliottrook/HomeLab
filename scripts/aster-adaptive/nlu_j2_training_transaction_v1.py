"""Compose the admitted J2 training, selection, artifact and replay transaction.

This module is inert until explicitly invoked.  It has no network, routing,
tool or deployment path and never reads the sealed evaluation corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import nlu_j2_artifact_contract_v1 as artifact_contract
import nlu_j2_corpus_v1 as corpus_contract
import nlu_j2_reference_forward_v1 as forward
import nlu_j2_reference_primitives_v1 as primitives
import nlu_j2_reference_training_v1 as training
import nlu_j2_replay_contract_v1 as replay_contract
import nlu_j2_training_admission_v1 as admission_contract
import nlu_j2_training_recipe_manifest_v1 as recipe_contract
import nlu_j2_validation_selection_v1 as selection
from nlu_threshold_policy import decode_unique_json


CORPUS_SHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
CORPUS_RELEASE_SHA256 = (
    "1f0e7d3777746e23472b0daa85dc7d103da0ac7ce09fe192e1c0f44dd0abe710"
)
VALIDATION_TRUTH_SHA256 = (
    "cfb58d9bb29667a762b01c246f3e52e0d5a9d29158aab21f22831bde573c2eab"
)
OUTPUT_NAMES = (
    "artifact.json", "validation-truth.json", "validation-selection.json",
    "replay-clean-cpu-1.json", "replay-clean-cpu-2.json",
    "training-transaction.json",
)
FAILURE_NAMES = ("failure.json",)
FORBIDDEN_AUDIT_PREFIXES = ("socket.", "ssl.")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _audit(event: str, _args: tuple[object, ...]) -> None:
    if event.startswith(FORBIDDEN_AUDIT_PREFIXES):
        raise RuntimeError("network access is forbidden during J2 training")


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


def _load_inputs(corpus_raw: bytes, release_raw: bytes,
                 admission_raw: bytes, recipe_raw: bytes) -> dict[str, object]:
    """Validate exact retained identities and return the frozen data split."""
    admitted = admission_contract.validate_result(admission_raw)
    recipe = recipe_contract.validate(recipe_raw)
    if (_sha256(corpus_raw) != CORPUS_SHA256
            or _sha256(release_raw) != CORPUS_RELEASE_SHA256
            or recipe["manifest_sha256"]
            != admission_contract.EXPECTED_RESULT["training_recipe_sha256"]):
        raise ValueError("J2 training transaction input identity changed")
    release = decode_unique_json(release_raw)
    if (not isinstance(release, dict)
            or release.get("corpus_sha256") != CORPUS_SHA256
            or release.get("training_authorized") is not False
            or release.get("authority") != "not-granted"
            or release.get("automatic_routing") != "off"):
        raise ValueError("J2 corpus release boundary changed")
    corpus = decode_unique_json(corpus_raw)
    if (not isinstance(corpus, dict)
            or set(corpus) != {"schema", "manifest_sha256", "data_class",
                               "evidence_class", "ontology_sha256", "custodian",
                               "authority", "cases"}
            or corpus["schema"] != corpus_contract.SCHEMA
            or corpus["manifest_sha256"] != corpus_contract.MANIFEST_SHA256
            or corpus["data_class"] != corpus_contract.DATA_CLASS
            or corpus["evidence_class"] != corpus_contract.EVIDENCE_CLASS
            or corpus["ontology_sha256"] != corpus_contract.ontology_sha256()
            or corpus["custodian"] != corpus_contract.CUSTODIAN
            or corpus["authority"] != "not-granted"
            or not isinstance(corpus["cases"], list)
            or len(corpus["cases"]) != 960):
        raise ValueError("J2 admitted corpus shape changed")
    train_rows, validation_rows, identifiers = [], [], set()
    for case in corpus["cases"]:
        if (not isinstance(case, dict)
                or set(case) != {"id", "split", "text", "label_id"}
                or not isinstance(case["id"], str)
                or corpus_contract.CASE_ID.fullmatch(case["id"]) is None
                or case["id"] in identifiers
                or case["split"] not in {"train", "validation"}
                or not case["id"].startswith(f"j2-{case['split']}-")
                or not isinstance(case["text"], str) or not case["text"]
                or case["label_id"] not in forward.LABELS):
            raise ValueError("J2 admitted corpus row changed")
        identifiers.add(case["id"])
        row = {"id": case["id"], "text": case["text"],
               "label_id": case["label_id"]}
        (train_rows if case["split"] == "train" else validation_rows).append(row)
    train_rows.sort(key=lambda row: row["id"])
    validation_rows.sort(key=lambda row: row["id"])
    training.epoch_batches(train_rows)
    truth_raw = artifact_contract.canonical({
        "schema": "aster-nlu-j2-validation-truth.v1",
        "rows": validation_rows,
        "authority": "none",
        "automatic_routing": "off",
    })
    replay_contract._truth(truth_raw)
    if _sha256(truth_raw) != VALIDATION_TRUTH_SHA256:
        raise ValueError("J2 retained validation truth identity changed")
    return {
        "train_rows": train_rows,
        "validation_rows": validation_rows,
        "validation_truth_raw": truth_raw,
        "training_admission_sha256": admitted["training_admission_sha256"],
    }


def _initial_tensors() -> dict[str, list[float]]:
    return {name: list(values)
            for name, _shape, values in primitives.initialized_parameters()}


def _guarded_exact(text: str, predicted: str, expected: str) -> bool:
    return (replay_contract._guarded(text, predicted)
            == replay_contract._guarded(text, expected))


def _validate_epoch(epoch: int, rows: list[dict[str, object]],
                    tensors: dict[str, list[float]]) -> dict[str, object]:
    raw_exact = guarded_exact = 0
    loss = 0.0
    for row in rows:
        result = forward.forward(row["text"], tensors)
        target = forward.LABELS.index(row["label_id"])
        probability = result["probabilities"][target]
        if not 0.0 < probability <= 1.0:
            raise ValueError("J2 validation probability changed")
        loss -= math.log(probability)
        exact = result["label_id"] == row["label_id"]
        raw_exact += exact
        guarded_exact += exact and _guarded_exact(
            row["text"], result["label_id"], row["label_id"])
    return {"epoch": epoch, "rows": 192,
            "raw_exact_count": raw_exact,
            "guarded_exact_count": guarded_exact,
            "mean_validation_loss": round(loss / 192, 12)}


def _quantized(tensors: dict[str, list[float]]) -> dict[str, list[float]]:
    result = {}
    for name in training.PARAMETER_ORDER:
        values = [round(value, 10) for value in tensors[name]]
        if any(not math.isfinite(value) for value in values):
            raise ValueError("J2 quantized tensor is nonfinite")
        result[name] = values
    return result


def _threshold_rejection(selected_epoch: int,
                         summaries: list[dict[str, object]],
                         records: list[dict[str, object]]) -> dict[str, bytes]:
    safe = []
    for step in range(201):
        threshold = step / 200
        accepted = [row for row in records if row["margin"] >= threshold]
        if all(row["raw_exact"] and row["guarded_exact"] for row in accepted):
            safe.append((len(accepted), threshold))
    maximum_safe, best_threshold = max(safe, default=(0, 1.0))
    summary = next(row for row in summaries if row["epoch"] == selected_epoch)
    return {"failure.json": artifact_contract.canonical({
        "schema": "aster-nlu-j2-training-transaction-failure.v1",
        "status": "no-go",
        "first_failure_phase": "threshold-selection",
        "failure_class": "CANDIDATE_REJECTED",
        "failure_code": "NO_ELIGIBLE_VALIDATION_THRESHOLD",
        "epochs_completed": 40,
        "selected_epoch": selected_epoch,
        "selected_raw_exact_count": summary["raw_exact_count"],
        "selected_guarded_exact_count": summary["guarded_exact_count"],
        "maximum_safe_accepted": maximum_safe,
        "best_safe_threshold": best_threshold,
        "minimum_required": 116,
        "artifact_written": False,
        "production_changed": False,
        "sealed_evaluation_access": False,
        "authority": "none",
        "automatic_routing": "off",
        "deployment": False,
    })}


def train(corpus_raw: bytes, release_raw: bytes, admission_raw: bytes,
          recipe_raw: bytes) -> dict[str, bytes]:
    """Perform the complete deterministic training and emit inert evidence."""
    inputs = _load_inputs(corpus_raw, release_raw, admission_raw, recipe_raw)
    tensors = _initial_tensors()
    optimizer = training.optimizer_state()
    checkpoints: dict[int, dict[str, list[float]]] = {}
    summaries = []
    step = 0
    for epoch in range(1, 41):
        for batch in training.epoch_batches(inputs["train_rows"]):
            _loss, gradients = training.mean_gradients(batch, tensors)
            step += 1
            tensors, optimizer = training.apply_batch(
                tensors, gradients, optimizer, step)
        checkpoints[epoch] = {name: list(values)
                              for name, values in tensors.items()}
        summaries.append(_validate_epoch(
            epoch, inputs["validation_rows"], tensors))

    selected_epoch = selection.select_epoch(summaries)
    selected_tensors = _quantized(checkpoints[selected_epoch])
    _replay_rows, threshold_rows = replay_contract._recomputed_records(
        inputs["validation_rows"], selected_tensors, 0.0, forward.forward)
    try:
        selected_threshold = selection.select_threshold(threshold_rows)
    except ValueError as exc:
        if str(exc) == "J2 has no eligible validation threshold":
            return _threshold_rejection(
                selected_epoch, summaries, threshold_rows)
        raise
    replay_rows, threshold_rows = replay_contract._recomputed_records(
        inputs["validation_rows"], selected_tensors,
        selected_threshold["threshold"], forward.forward)
    tensors_raw = artifact_contract.canonical(selected_tensors)
    selection_value = {
        "schema": "aster-nlu-j2-validation-selection.v1",
        "validation_truth_sha256": _sha256(inputs["validation_truth_raw"]),
        "checkpoint_tensors_sha256": _sha256(tensors_raw),
        "selected_epoch": selected_epoch,
        "epoch_summaries": summaries,
        "threshold_records_sha256": replay_contract.records_sha256(threshold_rows),
        "threshold": selected_threshold["threshold"],
        "accepted_validation_rows": selected_threshold["accepted"],
        "validation_rows": 192,
        "minimum_accepted": 116,
        "all_accepted_raw_and_guarded_exact": True,
        "authority": "none",
        "automatic_routing": "off",
    }
    selection_raw = artifact_contract.canonical(selection_value)
    artifact = {
        "schema": "aster-nlu-j2-byte-conv-artifact.v1",
        "candidate_id": "j2-byte-conv-joint-v1",
        "training_recipe_sha256": artifact_contract.RECIPE_SHA256,
        "preregistration_sha256": recipe_contract.PREREGISTRATION_SHA256,
        "corpus_release_sha256": _sha256(release_raw),
        "training_admission_sha256": inputs["training_admission_sha256"],
        "ontology_sha256": recipe_contract.expected_manifest()["runtime_boundary"]["ontology_sha256"],
        "deterministic_guard_sha256": recipe_contract.expected_manifest()["runtime_boundary"]["deterministic_guard_source_sha256"],
        "selected_epoch": selected_epoch,
        "threshold": selected_threshold["threshold"],
        "validation_rows": 192,
        "accepted_validation_rows": selected_threshold["accepted"],
        "validation_truth_sha256": _sha256(inputs["validation_truth_raw"]),
        "validation_selection_sha256": _sha256(selection_raw),
        "validation_replay_sha256": replay_contract.records_sha256(replay_rows),
        "tensors": selected_tensors,
        "authority": "none",
        "automatic_routing": "off",
        "deployment": False,
    }
    artifact["artifact_sha256"] = artifact_contract.artifact_sha256(artifact)
    artifact_raw = artifact_contract.canonical(artifact)
    replay_raws = []
    for run_id in ("clean-cpu-1", "clean-cpu-2"):
        replay_raws.append(artifact_contract.canonical({
            "schema": "aster-nlu-j2-validation-replay.v1",
            "artifact_sha256": artifact["artifact_sha256"],
            "run_id": run_id,
            "backend": "portable-python-cpu-reference",
            "cpu_threads": 1,
            "rows": 192,
            "records": replay_rows,
            "authority": "none",
            "automatic_routing": "off",
        }))
    replay_contract.validate(
        artifact_raw, replay_raws[0], replay_raws[1], _sha256(release_raw),
        inputs["training_admission_sha256"], inputs["validation_truth_raw"],
        selection_raw)
    receipt_raw = artifact_contract.canonical({
        "schema": "aster-nlu-j2-training-transaction.v1",
        "status": "complete",
        "training_steps": step,
        "epochs": 40,
        "selected_epoch": selected_epoch,
        "threshold": selected_threshold["threshold"],
        "accepted_validation_rows": selected_threshold["accepted"],
        "artifact_file_sha256": _sha256(artifact_raw),
        "validation_truth_sha256": _sha256(inputs["validation_truth_raw"]),
        "validation_selection_sha256": _sha256(selection_raw),
        "clean_cpu_reproductions": 2,
        "sealed_evaluation_access": False,
        "authority": "none",
        "automatic_routing": "off",
        "deployment": False,
    })
    return {
        "artifact.json": artifact_raw,
        "validation-truth.json": inputs["validation_truth_raw"],
        "validation-selection.json": selection_raw,
        "replay-clean-cpu-1.json": replay_raws[0],
        "replay-clean-cpu-2.json": replay_raws[1],
        "training-transaction.json": receipt_raw,
    }


def _worker(corpus: Path, release: Path, admission: Path, recipe: Path,
            output: Path) -> None:
    if not output.is_dir() or any(output.iterdir()):
        raise ValueError("J2 worker output directory must exist and be empty")
    sys.addaudithook(_audit)
    values = train(corpus.read_bytes(), release.read_bytes(),
                   admission.read_bytes(), recipe.read_bytes())
    if set(values) != set(OUTPUT_NAMES) and set(values) != set(FAILURE_NAMES):
        raise ValueError("J2 worker output set changed")
    for name in values:
        _write_exclusive(output / name, values[name])


def _replay_worker(artifact_path: Path, truth_path: Path, run_id: str,
                   output_path: Path) -> None:
    if run_id not in {"clean-cpu-1", "clean-cpu-2"} or output_path.exists():
        raise ValueError("J2 replay worker boundary changed")
    sys.addaudithook(_audit)
    artifact = decode_unique_json(artifact_path.read_bytes())
    truth = replay_contract._truth(truth_path.read_bytes())
    rows, _selection_rows = replay_contract._recomputed_records(
        truth, artifact["tensors"], artifact["threshold"], forward.forward)
    raw = artifact_contract.canonical({
        "schema": "aster-nlu-j2-validation-replay.v1",
        "artifact_sha256": artifact["artifact_sha256"],
        "run_id": run_id,
        "backend": "portable-python-cpu-reference",
        "cpu_threads": 1,
        "rows": 192,
        "records": rows,
        "authority": "none",
        "automatic_routing": "off",
    })
    _write_exclusive(output_path, raw)


def _clean_environment() -> dict[str, str]:
    return {"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0",
            "LC_ALL": "C", "LANG": "C", "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def _run(command: list[str], *, cwd: Path, timeout: int) -> None:
    completed = subprocess.run(
        command, cwd=cwd, env=_clean_environment(), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
        check=False)
    if completed.returncode or completed.stdout or completed.stderr:
        raise RuntimeError("isolated J2 worker failed closed")


def execute(corpus: Path, release: Path, admission: Path, recipe: Path,
            output: Path) -> dict[str, object]:
    """Run training once and verify replay in two new isolated interpreters."""
    if output.exists():
        raise ValueError("J2 retained output directory already exists")
    output.mkdir(mode=0o700, parents=False)
    phase = "training-worker"
    script = Path(__file__).resolve()
    try:
        with tempfile.TemporaryDirectory(prefix="aster-j2-training-") as temporary:
            temporary_path = Path(temporary)
            trained = temporary_path / "trained"
            trained.mkdir(mode=0o700)
            _run([
                sys.executable, "-I", "-B", str(script), "--worker",
                "--corpus", str(corpus.resolve()),
                "--release", str(release.resolve()),
                "--admission", str(admission.resolve()),
                "--recipe", str(recipe.resolve()),
                "--output", str(trained),
            ], cwd=temporary_path, timeout=21600)
            trained_names = {path.name for path in trained.iterdir()}
            if trained_names == set(FAILURE_NAMES):
                raw = (trained / "failure.json").read_bytes()
                failure = decode_unique_json(raw)
                if (not isinstance(failure, dict)
                        or failure.get("status") != "no-go"
                        or failure.get("production_changed") is not False
                        or failure.get("sealed_evaluation_access") is not False
                        or failure.get("authority") != "none"
                        or failure.get("automatic_routing") != "off"
                        or failure.get("deployment") is not False):
                    raise RuntimeError("isolated J2 failure evidence changed")
                _write_exclusive(output / "failure.json", raw)
                return failure
            if trained_names != set(OUTPUT_NAMES):
                raise RuntimeError("isolated J2 worker output set changed")
            for number in (1, 2):
                phase = f"clean-replay-{number}"
                replay_path = temporary_path / f"replay-{number}.json"
                _run([
                    sys.executable, "-I", "-B", str(script), "--replay-worker",
                    "--artifact", str(trained / "artifact.json"),
                    "--truth", str(trained / "validation-truth.json"),
                    "--run-id", f"clean-cpu-{number}",
                    "--replay-output", str(replay_path),
                ], cwd=temporary_path, timeout=3600)
                expected = (trained / f"replay-clean-cpu-{number}.json").read_bytes()
                if replay_path.read_bytes() != expected:
                    raise RuntimeError("isolated J2 replay differs")
            phase = "retention"
            for name in OUTPUT_NAMES:
                _write_exclusive(output / name, (trained / name).read_bytes())
        receipt = decode_unique_json((output / "training-transaction.json").read_bytes())
        return receipt
    except BaseException as exc:
        # Preserve a bounded, content-free terminal record.  Never overwrite or
        # silently remove an uncertain partial output directory.
        failure = artifact_contract.canonical({
            "schema": "aster-nlu-j2-training-transaction-failure.v1",
            "status": "no-go", "first_failure_phase": phase,
            "failure_class": type(exc).__name__,
            "production_changed": False, "sealed_evaluation_access": False,
            "authority": "none", "automatic_routing": "off",
            "deployment": False,
        })
        try:
            _write_exclusive(output / "failure.json", failure)
        except FileExistsError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--replay-worker", action="store_true")
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--release", type=Path)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--recipe", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--truth", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--replay-output", type=Path)
    args = parser.parse_args()
    if args.worker:
        if args.replay_worker or None in {
                args.corpus, args.release, args.admission, args.recipe, args.output}:
            parser.error("complete exclusive J2 worker arguments are required")
        _worker(args.corpus, args.release, args.admission, args.recipe, args.output)
        return 0
    if args.replay_worker:
        if None in {args.artifact, args.truth, args.run_id, args.replay_output}:
            parser.error("complete J2 replay worker arguments are required")
        _replay_worker(args.artifact, args.truth, args.run_id, args.replay_output)
        return 0
    if None in {args.corpus, args.release, args.admission, args.recipe, args.output}:
        parser.error("complete J2 execution arguments are required")
    receipt = execute(args.corpus, args.release, args.admission,
                      args.recipe, args.output)
    if receipt["status"] == "no-go":
        summary = {key: receipt[key] for key in (
            "status", "first_failure_phase", "failure_class", "failure_code",
            "epochs_completed", "selected_epoch", "selected_raw_exact_count",
            "selected_guarded_exact_count", "maximum_safe_accepted",
            "best_safe_threshold", "minimum_required", "artifact_written",
            "production_changed", "sealed_evaluation_access", "authority",
            "automatic_routing", "deployment")}
    else:
        summary = {
            "status": receipt["status"], "epochs": receipt["epochs"],
            "selected_epoch": receipt["selected_epoch"],
            "accepted_validation_rows": receipt["accepted_validation_rows"],
            "authority": receipt["authority"],
            "automatic_routing": receipt["automatic_routing"],
            "deployment": receipt["deployment"],
        }
    print(artifact_contract.canonical(summary).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
