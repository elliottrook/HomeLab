"""Validate the source-only deterministic J2 training-recipe manifest.

This module defines no trainer and consumes no corpus or evaluation content.
It freezes the byte-convolution recipe that a later independently reviewed
implementation must reproduce exactly.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j2-training-recipe-manifest.v1"
PREREGISTRATION_SHA256 = (
    "2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee"
)
AUTHORITY = "not-granted"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _source_sha256(name: str) -> str:
    return sha256(Path(__file__).with_name(name).read_bytes())


def expected_manifest() -> dict[str, object]:
    """Return the complete frozen recipe contract."""
    return {
        "schema": SCHEMA,
        "candidate_id": "j2-byte-conv-joint-v1",
        "preregistration_sha256": PREREGISTRATION_SHA256,
        "status": "source-only-not-trained",
        "input": {
            "source_type": "unicode-string",
            "encoding": "utf-8-strict",
            "normalization": "none",
            "empty_input": "reject",
            "input_bytes": 512,
            "overlength": "keep-first-512-encoded-bytes",
            "truncated_utf8_suffix": "allowed-as-bytes-no-redecode",
            "padding": "right",
            "byte_ids": "0..255",
            "padding_token_id": 256,
            "vocabulary_size": 257,
        },
        "architecture": {
            "family": "byte-level-convolutional-joint-label",
            "embedding": {
                "dimension": 32,
                "byte_rows": "trainable",
                "padding_row": "fixed-zero-excluded-from-optimizer",
            },
            "convolution": {
                "widths": [3, 5, 7],
                "channels_per_width": 48,
                "stride": 1,
                "dilation": 1,
                "padding": "same-zero-symmetric",
                "operation": "cross-correlation-not-kernel-reversal",
                "weight_layout": "width-input-channel-output-channel",
                "sequence_layout": "position-embedding-channel",
                "padded_positions_participate_in_pooling": True,
                "activation": "relu",
                "bias": True,
            },
            "pooling": "global-max-over-512-positions-per-channel",
            "pooled_dimension": 144,
            "hidden": {"dimension": 96, "activation": "relu", "bias": True},
            "output": {
                "labels": 16,
                "label_order": sorted(ontology.CATALOGUE),
                "activation": "softmax",
                "bias": True,
            },
            "dropout": 0.0,
            "batch_normalization": False,
            "pretrained_weights": False,
        },
        "initialization": {
            "seed": 20261104,
            "prng": "splitmix64-v1",
            "uniform_conversion": "high-53-bits-divided-by-2^53",
            "parameter_dtype": "ieee754-binary64",
            "weight_rule": "xavier-uniform-sqrt(6/(fan_in+fan_out))",
            "weight_interval": "[-limit,+limit)",
            "bias_rule": "zeros",
            "tensor_scalar_order": "row-major-last-dimension-fastest",
            "fan_in_out": {
                "byte-embedding": [257, 32],
                "conv-width-3-weight": [96, 144],
                "conv-width-5-weight": [160, 240],
                "conv-width-7-weight": [224, 336],
                "hidden-weight": [144, 96],
                "output-weight": [96, 16],
            },
            "initialization_replay_sha256":
                "4d239c77ad73dc5cbbf060cb0bdf275a7095183217c1c076417d0fd46a2c09d1",
            "parameter_order": [
                "byte-embedding",
                "conv-width-3-weight", "conv-width-3-bias",
                "conv-width-5-weight", "conv-width-5-bias",
                "conv-width-7-weight", "conv-width-7-bias",
                "hidden-weight", "hidden-bias", "output-weight", "output-bias",
            ],
        },
        "training": {
            "train_rows": 768,
            "validation_rows": 192,
            "loss": "mean-categorical-cross-entropy",
            "loss_numerics": "max-shifted-log-softmax",
            "optimizer": {
                "name": "adamw",
                "learning_rate": 0.001,
                "learning_rate_schedule": "constant",
                "beta1": 0.9,
                "beta2": 0.999,
                "epsilon": 1e-8,
                "weight_decay": 0.0001,
                "weight_decay_scope": "weights-not-biases",
                "state_initialization": "first-and-second-moments-zero",
                "bias_correction": True,
                "epsilon_placement": "outside-sqrt",
                "step_order": "adam-bias-corrected-gradient-then-decoupled-weight-decay",
            },
            "epochs": 40,
            "batch_size": 32,
            "row_order": "case-id-lexicographic-every-epoch",
            "shuffle": False,
            "drop_last": False,
            "gradient_clipping": "none",
            "backward_pass": "explicit-architecture-specific-binary64",
            "relu_derivative_at_zero": 0.0,
            "global_max_tie_gradient": "lowest-sequence-position-only",
            "batch_update_boundary": "one-adamw-step-after-complete-batch-mean",
            "early_stopping": False,
            "checkpoint": "after-each-complete-epoch",
            "validation_gradient_access": False,
            "numeric_dtype": "ieee754-binary64",
            "reduction_order": "row-then-frozen-parameter-order-then-scalar-index",
            "cpu_threads": 1,
            "accelerator": "forbidden",
            "network": "forbidden",
            "evaluation_inputs": "forbidden",
            "sealed_holdout": "forbidden",
        },
        "validation_selection": {
            "source": "frozen-192-row-validation-only",
            "checkpoint_metric": "guarded-joint-label-exact-count-desc",
            "checkpoint_tie_breakers": [
                "raw-joint-label-exact-count-desc",
                "mean-validation-loss-rounded-12-decimals-asc",
                "epoch-asc",
            ],
            "confidence": "softmax-top1-probability",
            "margin": "softmax-top1-minus-top2",
            "threshold_signal": "margin",
            "threshold_grid": {
                "minimum": 0.0, "maximum": 1.0,
                "step": 0.005, "inclusive": True,
            },
            "minimum_accepted": 116,
            "accepted_row_requirement": "raw-label-and-guarded-interpretation-exact",
            "threshold_objective": "maximum-exact-coverage-then-lowest-threshold",
            "no_eligible_checkpoint_or_threshold": "reject-candidate",
            "public_or_sealed_evaluation_selection": "forbidden",
        },
        "artifact": {
            "schema": "aster-nlu-j2-byte-conv-artifact.v1",
            "required_bindings": [
                "training-recipe-manifest-sha256", "preregistration-sha256",
                "corpus-release-sha256", "ontology-sha256",
                "deterministic-guard-sha256", "validation-truth-sha256",
                "validation-selection-sha256",
            ],
            "weight_quantization": {
                "decimal_places": 10,
                "rounding": "nearest-ties-to-even",
                "nonfinite": "reject",
            },
            "serializer": "utf8-json-sort-keys-compact-newline",
            "self_hash": "sha256-excluding-artifact_sha256-field",
            "externally_pinned_artifact_digest_required": True,
            "replay": {
                "rows": 192,
                "record_fields": [
                    "id", "label_id", "confidence", "margin",
                    "guarded_interpretation", "accepted",
                ],
                "require_exact_record_equality_after_reload": True,
                "require_two_clean_cpu_reproductions": True,
                "recompute_from_validation_truth": True,
                "recompute_selection_receipt": True,
            },
        },
        "runtime_boundary": {
            "ontology_source_sha256": _source_sha256("nlu_whole_label_choice_v1.py"),
            "ontology_sha256": sha256(ontology._catalogue_text().encode()),
            "deterministic_guard_source_sha256": _source_sha256(
                "nlu_deterministic_guard_v1.py"),
            "reference_primitives_source_sha256": _source_sha256(
                "nlu_j2_reference_primitives_v1.py"),
            "reference_forward_source_sha256": _source_sha256(
                "nlu_j2_reference_forward_v1.py"),
            "validation_selection_source_sha256": _source_sha256(
                "nlu_j2_validation_selection_v1.py"),
            "training_math_source_sha256": _source_sha256(
                "nlu_j2_training_math_v1.py"),
            "reference_training_source_sha256": _source_sha256(
                "nlu_j2_reference_training_v1.py"),
            "guard_projection": "preserve-coherent-label-unless-strictly-more-restrictive",
            "personal_sensitivity_floor": True,
            "coherent_joint_label_only": True,
            "backend": "portable-python-cpu-reference",
            "model_backend_change": "forbidden",
            "tools": "forbidden",
            "route_effects": "forbidden",
            "deployment": "forbidden",
        },
        "prohibitions": [
            "train-during-manifest-validation",
            "embed-corpus-or-evaluation-content",
            "use-j1-artifact-or-weights",
            "use-j1-public-failures-for-training-or-selection",
            "open-existing-sealed-holdout",
            "network-or-pretrained-weights",
            "evaluation-driven-repair-or-retry",
        ],
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    expected = expected_manifest()
    if value != expected:
        raise ValueError("J2 training-recipe manifest differs from the frozen contract")
    text = raw.decode("utf-8")
    if "606bd761857f39932862df16780521a7ba4ba4923a9bd26b39ba44d9d7e7ae7c" in text:
        raise ValueError("J2 recipe embeds the forbidden J1 artifact identity")
    return {
        "schema": SCHEMA,
        "candidate_id": expected["candidate_id"],
        "manifest_sha256": sha256(raw),
        "input_bytes": 512,
        "labels": 16,
        "train_rows": 768,
        "validation_rows": 192,
        "status": "source-only-not-trained",
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.manifest.read_bytes()), sort_keys=True,
                     separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
