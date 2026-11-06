"""Stage exact private inputs into an already built isolated J2 custody kit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


CORPUS = "j2-corpus-candidate-v4-20261104/corpus.json"
ROLE_FILES = {
    "corpus-custodian": (
        ("private", CORPUS, "corpus.json",
         "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"),
        ("private", "j2-corpus-candidate-v4-20261104/label-review-independent-ai.json",
         "label-review.json", "896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028"),
        ("private", "j2-corpus-candidate-v4-20261104/quality-review-independent-ai.json",
         "quality-review.json", "f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f"),
        ("repository", "scripts/aster-adaptive/fixtures/nlu-development-v1.json",
         "references/development-v1.json", "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"),
        ("private", "nlu-calibration-v1/cases.json", "references/calibration-v1.json",
         "6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e"),
        ("private", "nlu-calibration-v2/cases.json", "references/calibration-v2.json",
         "c865bb045fa157592429bf1c4bd20a5aadd7a3f8b40ed0aaa536150a300334df"),
        ("private", "nlu-calibration-v3/cases.json", "references/calibration-v3.json",
         "b55098df5b7e475b4360007669d3c3b788fc89a1ab6eacaf023df0948bee4455"),
        ("private", "nlu-calibration-v4/cases.json", "references/calibration-v4.json",
         "09f82238506e01b8e8e2b443dfaee566263344a020032862cfb1570e958079c3"),
        ("private", "nlu-calibration-v5/cases.json", "references/calibration-v5.json",
         "50b6a36b64e8942eb83dd8769f52c52b6fa4a0e7a1d42adeebd7be2c5157c676"),
        ("private", "nlu-calibration-v6/cases.json", "references/calibration-v6.json",
         "a0a85ba1e46e88c0a7557dcd8744530d336bef74f5cd1854d25ba31877a5da4d"),
        ("repository", "scripts/aster-adaptive/fixtures/nlu-j1-training-draft-v3.json",
         "references/j1-v3.json", "a625e6778b8c26fc99ae4336979e4be88dcf4662fe4f91dba7163cf7804277d5"),
    ),
    "evaluation-custodian": (
        ("private", CORPUS, "corpus.json",
         "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"),
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(repository: Path, private_root: Path, workspace: Path,
          role: str) -> dict[str, object]:
    if role not in ROLE_FILES:
        raise ValueError("unknown J2 custody role")
    manifest = workspace / "KIT-MANIFEST.json"
    if not manifest.is_file() or not (workspace / "PROMPT.md").is_file():
        raise ValueError("J2 custody kit is not built")
    inputs = workspace / "inputs"
    if not inputs.is_dir():
        raise ValueError("J2 custody kit has no inputs directory")
    prepared = []
    for source_class, relative_source, relative_target, expected in ROLE_FILES[role]:
        root = repository if source_class == "repository" else private_root
        source = root / relative_source
        target = inputs / relative_target
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"J2 custody source changed: {relative_target}")
        if target.exists():
            raise ValueError(f"J2 custody target already exists: {relative_target}")
        prepared.append((source, target, expected))
    copied = []
    try:
        for source, target, expected in prepared:
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with source.open("rb") as reader:
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    with os.fdopen(fd, "wb") as writer:
                        shutil.copyfileobj(reader, writer)
                        writer.flush()
                        os.fsync(writer.fileno())
                except BaseException:
                    target.unlink(missing_ok=True)
                    raise
            if sha256(target) != expected:
                raise ValueError("J2 custody staged copy changed")
            copied.append(target)
    except BaseException:
        for target in copied:
            target.unlink(missing_ok=True)
        raise
    return {
        "schema": "aster-nlu-j2-isolated-custody-input-stage.v1",
        "role": role,
        "files": {str(target.relative_to(workspace)): expected
                  for _, target, expected in prepared},
        "file_count": len(prepared),
        "content_returned": False,
        "authority": "not-granted",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--role", choices=sorted(ROLE_FILES), required=True)
    args = parser.parse_args()
    result = stage(args.repository.resolve(), args.private_root.resolve(),
                   args.workspace.resolve(), args.role)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
