"""Deterministic, non-authorizing recipe for the M3 J1 classifier.

It consumes only the frozen development corpus and exact private non-overlap
receipts. It never reads evaluation or sealed-holdout inputs and grants no
route or tool authority.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import math
import re
import unicodedata

import nlu_deterministic_guard_v1 as guard
import nlu_joint_training_nonoverlap_receipt_v1 as nonoverlap
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json

SCHEMA = "aster-nlu-j1-training-recipe.v1"
ARTIFACT_SCHEMA = "aster-nlu-j1-multinomial-artifact.v1"
CORPUS_SHA256 = "a625e6778b8c26fc99ae4336979e4be88dcf4662fe4f91dba7163cf7804277d5"
CORPUS_TEXT_SET_SHA256 = "b0f466221d401e6464493afcd5b6c088f342de31b852387b8972014b3e2eb192"
FEATURE_DIMENSION = 4096
ALPHA = 0.1
QUANTIZATION_DECIMALS = 10
MARGIN_GRID = tuple(round(step / 200, 3) for step in range(201))
MIN_VALIDATION_ACCEPTED = 48
VALIDATION_COUNT = 80
TOKEN = re.compile(r"[\w]+", re.UNICODE)
HEX64 = re.compile(r"[0-9a-f]{64}")
AUTHORITY = "not-granted"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def normalize(text: str) -> str:
    if not isinstance(text, str) or not text.strip() or len(text.encode()) > 4096:
        raise ValueError("invalid J1 input text")
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def feature_names(text: str) -> tuple[str, ...]:
    normalized = normalize(text)
    words = TOKEN.findall(normalized)
    features = ["bias", *("w:" + word for word in words)]
    features.extend("b:" + left + "_" + right for left, right in zip(words, words[1:]))
    bounded = "^" + normalized + "$"
    for size in (3, 4, 5):
        features.extend("c:" + bounded[index:index + size]
                        for index in range(max(0, len(bounded) - size + 1)))
    return tuple(features)


def feature_vector(text: str) -> dict[int, float]:
    counts: Counter[int] = Counter()
    for feature in feature_names(text):
        digest = hashlib.blake2b(feature.encode(), digest_size=8,
                                 person=b"aster-j1").digest()
        counts[int.from_bytes(digest, "big") % FEATURE_DIMENSION] += (
            1 if digest[0] & 1 else -1)
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {index: abs(value) / norm for index, value in sorted(counts.items()) if value}


def _softmax(scores: list[float]) -> list[float]:
    if not scores or any(not math.isfinite(score) for score in scores):
        raise ValueError("invalid model scores")
    maximum = max(scores)
    values = [math.exp(score - maximum) for score in scores]
    total = sum(values)
    return [value / total for value in values]


def train_rows(rows: list[dict[str, str]]) -> tuple[tuple[str, ...], dict[str, object]]:
    """Fit fixed-alpha multinomial likelihoods from development rows only."""
    labels = tuple(sorted(ontology.CATALOGUE))
    if not rows or any(set(row) != {"id", "text", "label_id"} for row in rows):
        raise ValueError("training rows differ from the fixed schema")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("training row identifiers are not unique")
    counts = {label: Counter() for label in labels}
    totals = Counter()
    for row in sorted(rows, key=lambda value: value["id"]):
        label = row["label_id"]
        if label not in counts:
            raise ValueError("training row has an unknown coherent label")
        features = feature_vector(row["text"])
        counts[label].update(features)
        totals[label] += sum(features.values())
    defaults, deltas = [], []
    for label in labels:
        denominator = totals[label] + ALPHA * FEATURE_DIMENSION
        default = math.log(ALPHA / denominator)
        defaults.append(default)
        deltas.append({index: math.log((value + ALPHA) / denominator) - default
                       for index, value in sorted(counts[label].items())})
    return labels, {"defaults": defaults, "deltas": deltas}


def quantize_model(model: dict[str, object]) -> dict[str, object]:
    defaults, deltas = model.get("defaults"), model.get("deltas")
    if (not isinstance(defaults, list) or not isinstance(deltas, list)
            or len(defaults) != len(ontology.CATALOGUE) or len(deltas) != len(defaults)):
        raise ValueError("model shape changed")
    result_deltas = []
    for row in deltas:
        if not isinstance(row, dict):
            raise ValueError("model delta row changed")
        values = {}
        for index, value in row.items():
            if type(index) is not int or not 0 <= index < FEATURE_DIMENSION:
                raise ValueError("model feature index changed")
            if type(value) not in {int, float} or not math.isfinite(value):
                raise ValueError("model delta is not finite")
            rounded = round(float(value), QUANTIZATION_DECIMALS)
            if rounded:
                values[index] = rounded
        result_deltas.append(values)
    rounded_defaults = [round(float(value), QUANTIZATION_DECIMALS) for value in defaults]
    if any(not math.isfinite(value) for value in rounded_defaults):
        raise ValueError("model defaults are not finite")
    return {"defaults": rounded_defaults, "deltas": result_deltas}


def predict(labels: tuple[str, ...], model: dict[str, object], text: str) -> dict[str, object]:
    if labels != tuple(sorted(ontology.CATALOGUE)):
        raise ValueError("prediction label map changed")
    model = quantize_model(model)
    features = feature_vector(text)
    mass = sum(features.values())
    scores = [model["defaults"][number] * mass + sum(
        model["deltas"][number].get(index, 0.0) * value
        for index, value in features.items()) for number in range(len(labels))]
    probabilities = _softmax(scores)
    order = sorted(range(len(labels)), key=lambda index: (-probabilities[index], labels[index]))
    winner, second = order[:2]
    return {"label_id": labels[winner], "confidence": probabilities[winner],
            "margin": probabilities[winner] - probabilities[second]}


def guarded_interpretation(text: str, label_id: str) -> dict[str, object]:
    """Apply the guard without broadening an already coherent catalogue label."""
    selected = copy.deepcopy(ontology.CATALOGUE[label_id])
    guarded = guard.apply(text, selected)
    restrictiveness = {"route": 0, "clarify": 0, "abstain": 1, "deny": 2}
    value = guarded if (restrictiveness[guarded["disposition"]]
                        > restrictiveness[selected["disposition"]]) else selected
    words = set(re.findall(r"[a-z]+", text.lower()))
    personal = {"my", "mine", "private", "personal", "journal", "medication",
                "appointment", "calendar", "inbox", "messages", "sleep", "bedtime",
                "unread", "account", "medical", "email", "mail", "location"}
    if words & personal:
        value["sensitivity"] = "personal"
    guard.contract._validate_semantics(value)
    return value


def _validate_prediction(row: dict[str, object]) -> None:
    if set(row) != {"id", "label_id", "expected_label_id", "confidence", "margin",
                    "guarded_exact"}:
        raise ValueError("validation prediction schema changed")
    if not isinstance(row["id"], str) or not row["id"]:
        raise ValueError("validation prediction ID changed")
    if row["label_id"] not in ontology.CATALOGUE or row["expected_label_id"] not in ontology.CATALOGUE:
        raise ValueError("validation prediction label changed")
    for field in ("confidence", "margin"):
        value = row[field]
        if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("validation prediction confidence changed")
    if row["margin"] > row["confidence"]:
        raise ValueError("validation prediction margin changed")
    if type(row["guarded_exact"]) is not bool:
        raise ValueError("validation guarded result changed")


def select_threshold(predictions: list[dict[str, object]], *, expected_count: int = VALIDATION_COUNT,
                     minimum_accepted: int = MIN_VALIDATION_ACCEPTED) -> float:
    """Choose maximum exact coverage on the preregistered validation margin grid."""
    if len(predictions) != expected_count or not 1 <= minimum_accepted <= expected_count:
        raise ValueError("validation prediction count changed")
    for row in predictions:
        _validate_prediction(row)
    if len({row["id"] for row in predictions}) != expected_count:
        raise ValueError("validation prediction IDs are not unique")
    best = None
    for threshold in MARGIN_GRID:
        accepted = [row for row in predictions if row["margin"] >= threshold]
        if (len(accepted) >= minimum_accepted
                and all(row["label_id"] == row["expected_label_id"]
                        and row["guarded_exact"] for row in accepted)):
            candidate = (len(accepted), -threshold, threshold)
            if best is None or candidate > best:
                best = candidate
    if best is None:
        raise ValueError("no exact validation margin meets the coverage floor")
    return best[2]


def _release_bindings(release_raw: bytes) -> dict[str, object]:
    value = decode_unique_json(release_raw)
    if (not isinstance(value, dict)
            or value.get("schema") != "aster-nlu-j1-training-release-candidate.v1"
            or value.get("authority") != AUTHORITY or value.get("automatic_routing") != "off"):
        raise ValueError("release-candidate boundary changed")
    corpus, private, runtime = (value.get("corpus", {}),
                                value.get("private_nonoverlap", {}),
                                value.get("runtime_boundary", {}))
    if (corpus.get("sha256") != CORPUS_SHA256
            or corpus.get("normalized_text_set_sha256") != CORPUS_TEXT_SET_SHA256
            or private.get("status") != "complete" or private.get("sealed_holdout_read") is not False
            or runtime.get("deterministic_guard_required") is not True):
        raise ValueError("release-candidate evidence binding changed")
    return value


def artifact(labels: tuple[str, ...], model: dict[str, object], *, margin_threshold: float,
             release_candidate_sha256: str, guard_sha256: str) -> dict[str, object]:
    if labels != tuple(sorted(ontology.CATALOGUE)):
        raise ValueError("artifact label map changed")
    if margin_threshold not in MARGIN_GRID:
        raise ValueError("artifact threshold is outside the frozen grid")
    if not HEX64.fullmatch(release_candidate_sha256) or not HEX64.fullmatch(guard_sha256):
        raise ValueError("artifact source binding changed")
    model = quantize_model(model)
    sparse = [{"label_id": label, "default": model["defaults"][number],
               "deltas": [[index, value] for index, value in model["deltas"][number].items()]}
              for number, label in enumerate(labels)]
    value = {"schema": ARTIFACT_SCHEMA, "recipe": SCHEMA,
             "corpus_sha256": CORPUS_SHA256,
             "corpus_normalized_text_set_sha256": CORPUS_TEXT_SET_SHA256,
             "ontology_sha256": hashlib.sha256(ontology._catalogue_text().encode()).hexdigest(),
             "release_candidate_sha256": release_candidate_sha256,
             "deterministic_guard_sha256": guard_sha256,
             "feature_dimension": FEATURE_DIMENSION, "alpha": ALPHA,
             "labels": sparse, "margin_threshold": margin_threshold,
             "minimum_validation_accepted": MIN_VALIDATION_ACCEPTED,
             "authority": AUTHORITY, "automatic_routing": "off", "artifact_sha256": ""}
    copied = dict(value); copied.pop("artifact_sha256")
    value["artifact_sha256"] = hashlib.sha256(canonical(copied)).hexdigest()
    return value


def model_from_artifact(value: dict[str, object], *, release_candidate_sha256: str,
                        guard_sha256: str, expected_artifact_sha256: str
                        ) -> tuple[tuple[str, ...], dict[str, object]]:
    if (not isinstance(value, dict) or value.get("schema") != ARTIFACT_SCHEMA
            or value.get("recipe") != SCHEMA
            or value.get("corpus_sha256") != CORPUS_SHA256
            or value.get("corpus_normalized_text_set_sha256") != CORPUS_TEXT_SET_SHA256
            or value.get("ontology_sha256")
            != hashlib.sha256(ontology._catalogue_text().encode()).hexdigest()
            or value.get("release_candidate_sha256") != release_candidate_sha256
            or value.get("deterministic_guard_sha256") != guard_sha256
            or value.get("feature_dimension") != FEATURE_DIMENSION
            or value.get("alpha") != ALPHA
            or value.get("minimum_validation_accepted") != MIN_VALIDATION_ACCEPTED
            or value.get("margin_threshold") not in MARGIN_GRID
            or value.get("authority") != AUTHORITY or value.get("automatic_routing") != "off"):
        raise ValueError("artifact boundary changed")
    copied = dict(value); digest = copied.pop("artifact_sha256", None)
    if (not HEX64.fullmatch(expected_artifact_sha256)
            or digest != expected_artifact_sha256
            or hashlib.sha256(canonical(copied)).hexdigest() != digest):
        raise ValueError("artifact digest changed")
    rows = value.get("labels")
    if not isinstance(rows, list) or len(rows) != len(ontology.CATALOGUE):
        raise ValueError("artifact labels changed")
    labels = tuple(row.get("label_id") for row in rows if isinstance(row, dict))
    if labels != tuple(sorted(ontology.CATALOGUE)):
        raise ValueError("artifact label order changed")
    defaults, deltas = [], []
    for row in rows:
        default, entries = row.get("default"), row.get("deltas")
        if type(default) not in {int, float} or not math.isfinite(default) or not isinstance(entries, list):
            raise ValueError("artifact likelihood row changed")
        mapped = {}
        for entry in entries:
            if (not isinstance(entry, list) or len(entry) != 2 or type(entry[0]) is not int
                    or not 0 <= entry[0] < FEATURE_DIMENSION or entry[0] in mapped
                    or type(entry[1]) not in {int, float} or not math.isfinite(entry[1])):
                raise ValueError("artifact likelihood entry changed")
            mapped[entry[0]] = float(entry[1])
        defaults.append(float(default)); deltas.append(mapped)
    return labels, quantize_model({"defaults": defaults, "deltas": deltas})


def project(value: dict[str, object], text: str, *, release_candidate_sha256: str,
            guard_sha256: str, expected_artifact_sha256: str) -> dict[str, object]:
    """Project one known label through the guard, or fail closed to abstain."""
    labels, model = model_from_artifact(value,
                                        release_candidate_sha256=release_candidate_sha256,
                                        guard_sha256=guard_sha256,
                                        expected_artifact_sha256=expected_artifact_sha256)
    prediction = predict(labels, model, text)
    accepted = prediction["margin"] >= value["margin_threshold"]
    if accepted:
        interpretation = guarded_interpretation(text, prediction["label_id"])
    else:
        interpretation = guard.apply(text, {
            "request_family": "unsupported", "sensitivity": "internal",
            "capability_needs": [], "ambiguity": "clear",
            "disposition": "abstain", "reason": "unsupported",
        })
    return {**prediction, "accepted": accepted, "interpretation": interpretation,
            "authority": AUTHORITY, "automatic_routing": "off"}


def train_exact(corpus_raw: bytes, receipt_raws: dict[str, bytes], private_result_raw: bytes,
                release_candidate_raw: bytes) -> tuple[dict[str, object], dict[str, object]]:
    """Train only the exact corpus and exact seven reviewed private receipts."""
    if hashlib.sha256(corpus_raw).hexdigest() != CORPUS_SHA256:
        raise ValueError("training corpus identity changed")
    release = _release_bindings(release_candidate_raw)
    expected_receipts = release["private_nonoverlap"].get("receipt_hashes")
    if (not isinstance(expected_receipts, dict) or set(receipt_raws) != set(expected_receipts)
            or any(hashlib.sha256(receipt_raws[name]).hexdigest() != digest
                   for name, digest in expected_receipts.items())):
        raise ValueError("private receipt bytes changed")
    if hashlib.sha256(private_result_raw).hexdigest() != release["private_nonoverlap"].get("result_sha256"):
        raise ValueError("private review result bytes changed")
    receipt_values, receipt_errors = nonoverlap.validate_set(receipt_raws)
    if receipt_errors or len(receipt_values) != 7:
        raise ValueError("seven valid non-overlap receipts are required")
    if any(value.get("subject_source_sha256") != CORPUS_SHA256
           or value.get("subject_normalized_text_set_sha256") != CORPUS_TEXT_SET_SHA256
           for value in receipt_values.values()):
        raise ValueError("non-overlap receipts bind a different training corpus")
    result = decode_unique_json(private_result_raw)
    if (not isinstance(result, dict) or result.get("status") != "complete"
            or result.get("reference_count") != 7 or result.get("receipts_written") != 7
            or result.get("sealed_holdout_read") is not False
            or result.get("subject_source_sha256") != CORPUS_SHA256):
        raise ValueError("private review result changed")
    value = decode_unique_json(corpus_raw)
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or len(cases) != 400:
        raise ValueError("training corpus must contain exactly 400 cases")
    training, validation = [], []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "split", "text", "label_id"}:
            raise ValueError("training corpus case schema changed")
        row = {"id": case["id"], "text": case["text"], "label_id": case["label_id"]}
        if case["split"] == "train": training.append(row)
        elif case["split"] == "validation": validation.append(row)
        else: raise ValueError("training corpus split changed")
    if len(training) != 320 or len(validation) != VALIDATION_COUNT:
        raise ValueError("training and validation partitions changed")
    labels, trained = train_rows(training)
    deployed = quantize_model(trained)
    predictions = []
    for row in sorted(validation, key=lambda item: item["id"]):
        prediction = predict(labels, deployed, row["text"])
        predictions.append({"id": row["id"], **prediction,
                            "expected_label_id": row["label_id"],
                            "guarded_exact": guarded_interpretation(
                                row["text"], prediction["label_id"])
                            == ontology.CATALOGUE[row["label_id"]]})
    threshold = select_threshold(predictions)
    release_sha = hashlib.sha256(release_candidate_raw).hexdigest()
    guard_sha = release["runtime_boundary"]["deterministic_guard_sha256"]
    model = artifact(labels, deployed, margin_threshold=threshold,
                     release_candidate_sha256=release_sha, guard_sha256=guard_sha)
    artifact_labels, artifact_model = model_from_artifact(
        model, release_candidate_sha256=release_sha, guard_sha256=guard_sha,
        expected_artifact_sha256=model["artifact_sha256"])
    replay = []
    for row in sorted(validation, key=lambda item: item["id"]):
        prediction = predict(artifact_labels, artifact_model, row["text"])
        replay.append({"id": row["id"], **prediction,
                       "expected_label_id": row["label_id"],
                       "guarded_exact": guarded_interpretation(
                           row["text"], prediction["label_id"])
                       == ontology.CATALOGUE[row["label_id"]]})
    if predictions != replay:
        raise ValueError("serialized artifact changed validation predictions")
    accepted = [row for row in replay if row["margin"] >= threshold]
    summary = {"schema": "aster-nlu-j1-training-summary.v1",
               "corpus_sha256": CORPUS_SHA256, "train_count": 320,
               "validation_count": VALIDATION_COUNT,
               "validation_exact": sum(row["label_id"] == row["expected_label_id"] for row in replay),
               "guarded_validation_exact": sum(row["guarded_exact"] for row in replay),
               "accepted_validation": len(accepted),
               "accepted_validation_exact": sum(row["label_id"] == row["expected_label_id"]
                                                and row["guarded_exact"] for row in accepted),
               "minimum_validation_accepted": MIN_VALIDATION_ACCEPTED,
               "margin_threshold": threshold, "artifact_sha256": model["artifact_sha256"],
               "release_candidate_sha256": release_sha,
               "authority": AUTHORITY, "automatic_routing": "off"}
    return model, summary


def recipe_manifest() -> dict[str, object]:
    return {"schema": SCHEMA, "corpus_sha256": CORPUS_SHA256,
            "corpus_normalized_text_set_sha256": CORPUS_TEXT_SET_SHA256,
            "feature_dimension": FEATURE_DIMENSION, "learner": "multinomial-likelihood",
            "alpha": ALPHA, "quantization_decimals": QUANTIZATION_DECIMALS,
            "margin_grid": list(MARGIN_GRID),
            "minimum_validation_accepted": MIN_VALIDATION_ACCEPTED,
            "train_split": 320, "validation_split": VALIDATION_COUNT,
            "backend": "portable-python-reference", "network": "forbidden",
            "evaluation_inputs": "forbidden", "sealed_holdout": "forbidden",
            "authority": AUTHORITY, "automatic_routing": "off"}


if __name__ == "__main__":
    print(json.dumps(recipe_manifest(), sort_keys=True, separators=(",", ":")))
