"""Build content-free source kits for the two isolated J2 custodians."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


SOURCE_FILES = (
    "nlu_j2_corpus_v1.py",
    "nlu_j2_custody_kit_v1.py",
    "nlu_j2_custody_receipt_v1.py",
    "nlu_j2_disjointness_proof_v1.py",
    "nlu_j2_evaluation_v1.py",
    "nlu_j2_external_proof_v1.py",
    "nlu_j2_label_review_v1.py",
    "nlu_j2_quality_review_v1.py",
    "nlu_threshold_policy.py",
    "nlu_whole_label_choice_v1.py",
)
PROMPTS = {
    "corpus-custodian": "M3-J2-CORPUS-CUSTODIAN-PROMPT-2026-11-06.md",
    "evaluation-custodian": "M3-J2-EVALUATION-CUSTODIAN-PROMPT-2026-11-06.md",
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(repository: Path, output: Path) -> dict[str, object]:
    source = repository / "scripts" / "aster-adaptive"
    evidence = repository / "docs" / "projects" / "AI Projects" / "evidence"
    if output.exists():
        raise ValueError("custody kit output already exists")
    output.mkdir(parents=True, mode=0o700)
    result = {}
    try:
        for role, prompt_name in PROMPTS.items():
            root = output / role
            root.mkdir(mode=0o700)
            (root / "inputs").mkdir(mode=0o700)
            (root / "private").mkdir(mode=0o700)
            (root / "export").mkdir(mode=0o700)
            inventory = {}
            for name in SOURCE_FILES:
                shutil.copyfile(source / name, root / name)
                inventory[name] = sha256(root / name)
            shutil.copyfile(evidence / prompt_name, root / "PROMPT.md")
            inventory["PROMPT.md"] = sha256(root / "PROMPT.md")
            manifest = {
                "schema": "aster-nlu-j2-isolated-custody-kit.v1",
                "role": role,
                "files": inventory,
                "private_inputs_in_manifest": False,
                "authority": "not-granted",
            }
            (root / "KIT-MANIFEST.json").write_bytes(canonical(manifest))
            os.chmod(root / "KIT-MANIFEST.json", 0o644)
            result[role] = {
                "manifest_sha256": sha256(root / "KIT-MANIFEST.json"),
                "file_count": len(inventory),
            }
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise
    return {"schema": "aster-nlu-j2-isolated-custody-kit-build.v1",
            "kits": result, "private_inputs_copied": False,
            "authority": "not-granted"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.repository.resolve(), args.output.resolve()),
                     sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
