"""Cross-bind every J2 source/data proof before owner training review."""
from __future__ import annotations

import hashlib

import nlu_j2_custody_receipt_v1 as custody
import nlu_j2_disjointness_proof_v1 as disjointness
import nlu_j2_external_proof_v1 as external
import nlu_j2_owner_acceptance_v1 as owner
import nlu_j2_training_recipe_manifest_v1 as recipe
from nlu_threshold_policy import decode_unique_json


LABEL_REVIEW_SHA256 = "896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028"
QUALITY_REVIEW_SHA256 = "f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f"
OWNER_ACCEPTANCE_FILE_SHA256 = "9e7eb6f76396088b5650647d0c7970b5659711ff94fd3c0c16fd504619bf393b"
# Exact public-key fingerprints accepted by Jason on 2026-11-06. These trust
# custody evidence only; they grant no training, routing, tool or deployment
# authority.
TRUSTED_KEYS: dict[str, str] = {
    "independent-j2-corpus-custodian":
        "47feec850ae4dc67443249edcbc5c134c767e293c6dcc4bbede5a31c2749574c",
    "independent-j2-evaluation-custodian":
        "46685b0ebd4e1bcf65bfae35df4858373b2f928fe3f81ab267bfa58cedfa9498",
}


def _release(raw: bytes, custody_raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "manifest_sha256", "corpus_sha256",
              "normalized_text_set_sha256", "label_review_sha256",
              "quality_review_sha256", "custody_receipt_sha256", "rows",
              "accepted", "corrected", "reference_count",
              "normalized_overlap", "corpus_release_eligible",
              "training_authorized", "authority", "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-nlu-j2-corpus-release-summary.v1"
            or value["manifest_sha256"] != custody.MANIFEST_SHA256
            or value["corpus_sha256"] != disjointness.CORPUS_SHA256
            or value["normalized_text_set_sha256"] != disjointness.CORPUS_SET_SHA256
            or value["label_review_sha256"] != LABEL_REVIEW_SHA256
            or value["quality_review_sha256"] != QUALITY_REVIEW_SHA256
            or value["custody_receipt_sha256"]
            != hashlib.sha256(custody_raw).hexdigest()
            or value["rows"] != 960 or value["accepted"] != 960
            or value["corrected"] != 0 or value["reference_count"] != 8
            or value["normalized_overlap"] != 0
            or value["corpus_release_eligible"] is not True
            or value["training_authorized"] is not False
            or value["authority"] != "not-granted"
            or value["automatic_routing"] != "off"):
        raise ValueError("J2 corpus release is not admission eligible")
    return value


def admit(release_raw: bytes, owner_raw: bytes, recipe_raw: bytes,
          corpus_receipt_raw: bytes, corpus_proof_raw: bytes,
          corpus_key: object,
          evaluation_receipt_raw: bytes, evaluation_proof_raw: bytes,
          evaluation_key: object,
          disjointness_receipt_raw: bytes,
          disjointness_proof_raw: bytes) -> dict[str, object]:
    corpus_receipt = custody.corpus_receipt(corpus_receipt_raw)
    evaluation_receipt = custody.evaluation_receipt(evaluation_receipt_raw)
    release = _release(release_raw, corpus_receipt_raw)
    accepted = owner.validate(owner_raw)
    if hashlib.sha256(owner_raw).hexdigest() != OWNER_ACCEPTANCE_FILE_SHA256:
        raise ValueError("J2 owner acceptance file is not the retained decision")
    recipe_result = recipe.validate(recipe_raw)
    corpus_key_sha256 = TRUSTED_KEYS.get(corpus_receipt["custodian_id"])
    evaluation_key_sha256 = TRUSTED_KEYS.get(evaluation_receipt["custodian_id"])
    if not corpus_key_sha256 or not evaluation_key_sha256:
        raise ValueError("J2 custodian key is not owner-pinned")
    corpus_signed = external.verify(
        corpus_proof_raw, corpus_receipt_raw, corpus_key,
        corpus_key_sha256, "corpus-custody")
    evaluation_signed = external.verify(
        evaluation_proof_raw, evaluation_receipt_raw, evaluation_key,
        evaluation_key_sha256, "evaluation-custody")
    disjoint = disjointness.verify(
        disjointness_receipt_raw, disjointness_proof_raw, evaluation_key,
        evaluation_key_sha256)
    role_ids = {corpus_receipt["custodian_id"], corpus_receipt["reviewer_id"],
                evaluation_receipt["custodian_id"]}
    if (len(role_ids) != 3
            or corpus_signed["signer_id"] != corpus_receipt["custodian_id"]
            or evaluation_signed["signer_id"]
            != evaluation_receipt["custodian_id"]
            or corpus_signed["signer_id"] == evaluation_signed["signer_id"]
            or corpus_signed["signer_key_sha256"]
            == evaluation_signed["signer_key_sha256"]
            or disjoint["evaluation_sha256"]
            != evaluation_receipt["evaluation_sha256"]
            or disjoint["evaluation_normalized_text_set_sha256"]
            != evaluation_receipt["normalized_text_set_sha256"]
            or corpus_receipt["corpus_sha256"] != release["corpus_sha256"]
            or corpus_receipt["normalized_text_set_sha256"]
            != release["normalized_text_set_sha256"]
            or corpus_receipt["label_review_sha256"]
            != release["label_review_sha256"]
            or corpus_receipt["quality_review_sha256"]
            != release["quality_review_sha256"]
            or release["corpus_sha256"] != accepted["corpus_sha256"]
            or release["normalized_text_set_sha256"]
            != accepted["normalized_text_set_sha256"]
            or release["label_review_sha256"]
            != accepted["label_review_sha256"]
            or release["quality_review_sha256"]
            != accepted["quality_review_sha256"]):
        raise ValueError("J2 admission cross-binding differs")
    return {
        "schema": "aster-nlu-j2-training-admission.v1",
        "status": "eligible-for-owner-training-effect-review",
        "manifest_sha256": custody.MANIFEST_SHA256,
        "training_recipe_sha256": recipe_result["manifest_sha256"],
        "corpus_release_file_sha256": hashlib.sha256(release_raw).hexdigest(),
        "owner_acceptance_file_sha256": hashlib.sha256(owner_raw).hexdigest(),
        "corpus_receipt_file_sha256": hashlib.sha256(corpus_receipt_raw).hexdigest(),
        "evaluation_receipt_file_sha256":
            hashlib.sha256(evaluation_receipt_raw).hexdigest(),
        "disjointness_receipt_file_sha256":
            hashlib.sha256(disjointness_receipt_raw).hexdigest(),
        "corpus_signer_key_sha256": corpus_signed["signer_key_sha256"],
        "evaluation_signer_key_sha256": evaluation_signed["signer_key_sha256"],
        "corpus_proof_file_sha256": hashlib.sha256(corpus_proof_raw).hexdigest(),
        "evaluation_proof_file_sha256":
            hashlib.sha256(evaluation_proof_raw).hexdigest(),
        "disjointness_proof_file_sha256":
            hashlib.sha256(disjointness_proof_raw).hexdigest(),
        "intersection_count": 0, "declared_roles_distinct": True,
        "signatures_verified": True, "training_authorized": False,
        "sealed_evaluation_access": False, "authority": "not-granted",
        "automatic_routing": "off", "deployment": False,
    }
