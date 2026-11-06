"""Create-only staging for the content-free J2 training-effect inputs."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_training_admission_v1 as admission
import nlu_j2_training_transaction_v1 as transaction


RELEASE = {
    "accepted": 960,
    "authority": "not-granted",
    "automatic_routing": "off",
    "corpus_release_eligible": True,
    "corpus_sha256": transaction.CORPUS_SHA256,
    "corrected": 0,
    "custody_receipt_sha256":
        "43a9820a6438405ab010b6e358db4800c02d4ac5df8c3569db24325f1c2e284e",
    "label_review_sha256": admission.LABEL_REVIEW_SHA256,
    "manifest_sha256":
        "2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee",
    "normalized_overlap": 0,
    "normalized_text_set_sha256":
        "a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0",
    "quality_review_sha256": admission.QUALITY_REVIEW_SHA256,
    "reference_count": 8,
    "rows": 960,
    "schema": "aster-nlu-j2-corpus-release-summary.v1",
    "training_authorized": False,
}


def stage(output: Path) -> dict[str, object]:
    if output.exists():
        raise ValueError("J2 training input stage already exists")
    release_raw = artifact.canonical(RELEASE)
    admission_raw = admission.canonical(admission.EXPECTED_RESULT)
    if (hashlib.sha256(release_raw).hexdigest()
            != transaction.CORPUS_RELEASE_SHA256):
        raise ValueError("J2 staged release identity changed")
    validated = admission.validate_result(admission_raw)
    output.mkdir(mode=0o700, parents=False)
    receipt = {
        "schema": "aster-nlu-j2-training-input-stage.v1",
        "release_file_sha256": hashlib.sha256(release_raw).hexdigest(),
        "admission_file_sha256": validated["training_admission_sha256"],
        "content_free": True,
        "training_started": False,
        "sealed_evaluation_access": False,
        "authority": "none",
        "automatic_routing": "off",
        "deployment": False,
    }
    try:
        transaction._write_exclusive(output / "corpus-release.json", release_raw)
        transaction._write_exclusive(output / "training-admission.json", admission_raw)
        transaction._write_exclusive(output / "stage-receipt.json",
                                     artifact.canonical(receipt))
    except BaseException:
        # Preserve any uncertain create-only partial stage for reconciliation.
        raise
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = stage(args.output)
    print(artifact.canonical(receipt).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
