"""Create signed, content-free J2 custody outputs in an isolated workspace."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import nlu_j2_corpus_v1 as corpus_boundary
import nlu_j2_custody_receipt_v1 as custody
import nlu_j2_disjointness_proof_v1 as disjointness
import nlu_j2_evaluation_v1 as evaluation_boundary
import nlu_j2_external_proof_v1 as external
import nlu_j2_label_review_v1 as label_review
import nlu_j2_quality_review_v1 as quality_review


CORPUS_SHA256 = evaluation_boundary.CORPUS_SHA256
CORPUS_SET_SHA256 = evaluation_boundary.CORPUS_SET_SHA256
LABEL_REVIEW_SHA256 = "896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028"
QUALITY_REVIEW_SHA256 = "f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f"


def canonical(value: object) -> bytes:
    return external.canonical(value)


def _exclusive_write(path: Path, raw: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _run(command: list[str], *, input_raw: bytes | None = None) -> bytes:
    result = subprocess.run(command, input=input_raw, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise ValueError(f"custody crypto command failed: {detail[:240]}")
    return result.stdout


def public_key(private_key: Path) -> dict[str, object]:
    output = _run(["openssl", "rsa", "-in", str(private_key),
                   "-noout", "-modulus"]).decode().strip()
    match = re.fullmatch(r"Modulus=([0-9A-Fa-f]{512})", output)
    if match is None:
        raise ValueError("custody private key is not RSA-2048")
    key = {"kty": "RSA", "n": match.group(1).lower(), "e": 65537}
    external.key_sha256(key)
    return key


def create_key(private_key: Path, public_key_path: Path) -> dict[str, object]:
    if private_key.exists() or public_key_path.exists():
        raise ValueError("custody key target already exists")
    private_key.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt",
         "rsa_keygen_bits:2048", "-out", str(private_key)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        private_key.unlink(missing_ok=True)
        raise ValueError("custody RSA key generation failed")
    os.chmod(private_key, 0o600)
    key = public_key(private_key)
    _exclusive_write(public_key_path, canonical(key), 0o644)
    return {"public_key_sha256": external.key_sha256(key),
            "private_key_retained": True, "authority": "not-granted"}


def receipt_hash(value: dict[str, object]) -> str:
    copied = dict(value)
    copied.pop("receipt_sha256", None)
    return hashlib.sha256(canonical(copied)).hexdigest()


def sign(payload_raw: bytes, private_key: Path, key: dict[str, object],
         signer_id: str, scope: str) -> bytes:
    fingerprint = external.key_sha256(key)
    statement = {
        "schema": "aster-nlu-j2-external-proof.v1",
        "proof_scope": scope,
        "signer_id": signer_id,
        "signer_key_sha256": fingerprint,
        "payload_sha256": hashlib.sha256(payload_raw).hexdigest(),
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "authority": "not-granted",
    }
    signature = _run(["openssl", "dgst", "-sha256", "-sign",
                      str(private_key)], input_raw=canonical(statement))
    if len(signature) != 256:
        raise ValueError("custody RSA signature length changed")
    proof = dict(statement)
    proof["signature_hex"] = signature.hex()
    raw = canonical(proof)
    external.verify(raw, payload_raw, key, fingerprint, scope)
    return raw


def _load_key(private_key: Path, public_key_path: Path) -> dict[str, object]:
    key = json.loads(public_key_path.read_text())
    if key != public_key(private_key):
        raise ValueError("custody public and private key differ")
    return key


def _references(values: list[str]) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for item in values:
        name, separator, path = item.partition("=")
        if not separator or name in result:
            raise ValueError("references must be unique name=path entries")
        result[name] = Path(path).read_bytes()
    return result


def corpus_outputs(args: argparse.Namespace) -> dict[str, object]:
    corpus_raw = args.corpus.read_bytes()
    label_raw = args.label_review.read_bytes()
    quality_raw = args.quality_review.read_bytes()
    if hashlib.sha256(corpus_raw).hexdigest() != CORPUS_SHA256:
        raise ValueError("accepted J2 corpus bytes changed")
    if hashlib.sha256(label_raw).hexdigest() != LABEL_REVIEW_SHA256:
        raise ValueError("accepted J2 label review bytes changed")
    if hashlib.sha256(quality_raw).hexdigest() != QUALITY_REVIEW_SHA256:
        raise ValueError("accepted J2 quality review bytes changed")
    summary = corpus_boundary.validate_corpus(corpus_raw, _references(args.reference))
    labels = label_review.validate(corpus_raw, label_raw)
    quality = quality_review.validate(corpus_raw, quality_raw)
    if (summary["normalized_text_set_sha256"] != CORPUS_SET_SHA256
            or labels["accepted"] != 960 or labels["corrected"] != 0
            or labels["release_eligible"] is not True
            or quality["release_eligible"] is not True):
        raise ValueError("accepted J2 corpus review facts changed")
    receipt = {
        "schema": "aster-nlu-j2-corpus-custody.v1",
        "manifest_sha256": custody.MANIFEST_SHA256,
        "custodian_id": corpus_boundary.CUSTODIAN,
        "reviewer_id": label_review.REVIEWER,
        "corpus_sha256": CORPUS_SHA256,
        "normalized_text_set_sha256": CORPUS_SET_SHA256,
        "label_review_sha256": LABEL_REVIEW_SHA256,
        "quality_review_sha256": QUALITY_REVIEW_SHA256,
        "train_rows": 768, "validation_rows": 192, "labels": 16,
        "overlap_reference_count": 8, "normalized_overlap": 0,
        "content_in_receipt": False, "authority": "not-granted",
    }
    receipt["receipt_sha256"] = receipt_hash(receipt)
    receipt_raw = canonical(receipt)
    custody.corpus_receipt(receipt_raw)
    key = _load_key(args.private_key, args.public_key)
    proof_raw = sign(receipt_raw, args.private_key, key,
                     corpus_boundary.CUSTODIAN, "corpus-custody")
    _exclusive_write(args.output / "corpus-custody-receipt.json", receipt_raw)
    _exclusive_write(args.output / "corpus-custody-proof.json", proof_raw)
    return {"status": "complete", "role": corpus_boundary.CUSTODIAN,
            "public_key_sha256": external.key_sha256(key),
            "receipt_file_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "proof_file_sha256": hashlib.sha256(proof_raw).hexdigest(),
            "content_returned": False, "authority": "not-granted"}


def evaluation_outputs(args: argparse.Namespace) -> dict[str, object]:
    corpus_raw = args.corpus.read_bytes()
    evaluation_raw = args.evaluation.read_bytes()
    summary = evaluation_boundary.validate(evaluation_raw, corpus_raw)
    receipt = {
        "schema": "aster-nlu-j2-evaluation-seal.v1",
        "manifest_sha256": custody.MANIFEST_SHA256,
        "custodian_id": evaluation_boundary.CUSTODIAN,
        "evaluation_sha256": summary["evaluation_sha256"],
        "normalized_text_set_sha256": summary["normalized_text_set_sha256"],
        "cases": 32, "labels": 16, "cases_per_label": 2,
        "sealed_before_training": True, "trainer_access": "forbidden",
        "content_in_receipt": False, "authority": "not-granted",
    }
    receipt["receipt_sha256"] = receipt_hash(receipt)
    receipt_raw = canonical(receipt)
    custody.evaluation_receipt(receipt_raw)
    disjoint = {
        "schema": "aster-nlu-j2-corpus-evaluation-disjointness.v1",
        "manifest_sha256": custody.MANIFEST_SHA256,
        "corpus_sha256": CORPUS_SHA256,
        "corpus_normalized_text_set_sha256": CORPUS_SET_SHA256,
        "evaluation_sha256": summary["evaluation_sha256"],
        "evaluation_normalized_text_set_sha256":
            summary["normalized_text_set_sha256"],
        "corpus_rows": 960, "evaluation_cases": 32,
        "intersection_count": 0,
        "comparison_algorithm": "normalized-utf8-exact-set-v1",
        "custodian_id": evaluation_boundary.CUSTODIAN,
        "content_in_receipt": False, "authority": "not-granted",
    }
    disjoint["receipt_sha256"] = receipt_hash(disjoint)
    disjoint_raw = canonical(disjoint)
    disjointness.validate_receipt(disjoint_raw)
    key = _load_key(args.private_key, args.public_key)
    receipt_proof = sign(receipt_raw, args.private_key, key,
                         evaluation_boundary.CUSTODIAN, "evaluation-custody")
    disjoint_proof = sign(disjoint_raw, args.private_key, key,
                          evaluation_boundary.CUSTODIAN,
                          "corpus-evaluation-disjointness")
    fingerprint = external.key_sha256(key)
    disjointness.verify(disjoint_raw, disjoint_proof, key, fingerprint)
    _exclusive_write(args.output / "evaluation-custody-receipt.json", receipt_raw)
    _exclusive_write(args.output / "evaluation-custody-proof.json", receipt_proof)
    _exclusive_write(args.output / "corpus-evaluation-disjointness-receipt.json",
                     disjoint_raw)
    _exclusive_write(args.output / "corpus-evaluation-disjointness-proof.json",
                     disjoint_proof)
    return {"status": "complete", "role": evaluation_boundary.CUSTODIAN,
            "public_key_sha256": fingerprint,
            "evaluation_receipt_file_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "evaluation_proof_file_sha256": hashlib.sha256(receipt_proof).hexdigest(),
            "disjointness_receipt_file_sha256": hashlib.sha256(disjoint_raw).hexdigest(),
            "disjointness_proof_file_sha256": hashlib.sha256(disjoint_proof).hexdigest(),
            "content_returned": False, "authority": "not-granted"}


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    sub = value.add_subparsers(dest="command", required=True)
    key = sub.add_parser("keygen")
    key.add_argument("--private-key", type=Path, required=True)
    key.add_argument("--public-key", type=Path, required=True)
    corpus = sub.add_parser("corpus")
    corpus.add_argument("--corpus", type=Path, required=True)
    corpus.add_argument("--label-review", type=Path, required=True)
    corpus.add_argument("--quality-review", type=Path, required=True)
    corpus.add_argument("--reference", action="append", default=[], required=True)
    evaluation = sub.add_parser("evaluation")
    evaluation.add_argument("--corpus", type=Path, required=True)
    evaluation.add_argument("--evaluation", type=Path, required=True)
    for command in (corpus, evaluation):
        command.add_argument("--private-key", type=Path, required=True)
        command.add_argument("--public-key", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    if args.command == "keygen":
        result = create_key(args.private_key, args.public_key)
    elif args.command == "corpus":
        result = corpus_outputs(args)
    else:
        result = evaluation_outputs(args)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
