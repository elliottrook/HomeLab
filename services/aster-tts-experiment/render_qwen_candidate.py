#!/usr/bin/env python3
"""Render fixed passages through a pinned qwentts.cpp CLI candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Optional


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, sort_keys=True, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def require_hash(path: Path, expected: str, label: str) -> None:
    if (not path.is_file() or path.is_symlink() or sha256_file(path) != expected):
        raise ValueError(f"{label} pin mismatch")


def render(
    plan_path: Path,
    config_path: Path,
    output: Path,
    binary: Path,
    model: Path,
    codec: Path,
    reference_wav: Path,
    reference_text: Path,
    device: str,
    passage_filter: Optional[str],
    repeats: tuple[int, ...],
    timeout: int,
) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if plan.get("schema") != "aster-tts-experiment-plan.v1":
        raise ValueError("invalid experiment plan")
    pins = config.get("artifact_pins", {})
    for path, key, label in (
        (binary, "binary_sha256", "binary"),
        (model, "model_sha256", "model"),
        (codec, "codec_sha256", "codec"),
        (reference_wav, "reference_wav_sha256", "reference WAV"),
        (reference_text, "reference_text_sha256", "reference text"),
    ):
        require_hash(path, pins.get(key, ""), label)
    if config.get("mode") != "base-clone" or not isinstance(config.get("seed"), int):
        raise ValueError("unsupported Qwen configuration")
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    selected = [item for item in plan["passages"]
                if passage_filter is None or item["id"] == passage_filter]
    if not selected:
        raise ValueError("passage filter matched nothing")
    completed = []
    for passage in selected:
        for repeat in repeats:
            stem = f"{passage['id']}-r{repeat}"
            temporary = output / f".{stem}.wav.partial"
            destination = output / f"{stem}.wav"
            command = [
                str(binary), "--model", str(model), "--codec", str(codec),
                "--device", device, "--lang", config["language"],
                "--ref-wav", str(reference_wav), "--ref-text", str(reference_text),
                "--seed", str(config["seed"]), "--format", "wav16",
                "-o", str(temporary),
            ]
            started = time.monotonic()
            try:
                result = subprocess.run(
                    command,
                    input=passage["normalized_text"] + "\n",
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    env={**os.environ, "GGML_BACKEND": device},
                )
            except subprocess.TimeoutExpired:
                temporary.unlink(missing_ok=True)
                raise RuntimeError(f"Qwen render timed out for {stem}") from None
            elapsed = time.monotonic() - started
            stderr = result.stderr[-32_768:]
            (output / f"{stem}.stderr.log").write_text(stderr, encoding="utf-8")
            os.chmod(output / f"{stem}.stderr.log", 0o600)
            if result.returncode != 0 or not temporary.is_file():
                temporary.unlink(missing_ok=True)
                raise RuntimeError(f"Qwen render failed for {stem}: exit {result.returncode}")
            os.chmod(temporary, 0o600)
            os.replace(temporary, destination)
            atomic_json(output / f"{stem}.timing.json", {
                "schema": "aster-tts-render-timing.v1",
                "render_seconds": round(elapsed, 6),
                "device": device,
                "seed": config["seed"],
                "input_sha256": passage["normalized_sha256"],
                "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
            })
            completed.append(stem)
    return {"state": "complete", "config_id": config["id"],
            "device": device, "renders": completed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--codec", type=Path, required=True)
    parser.add_argument("--reference-wav", type=Path, required=True)
    parser.add_argument("--reference-text", type=Path, required=True)
    parser.add_argument("--device", default="CPU")
    parser.add_argument("--passage")
    parser.add_argument("--repeat", type=int, action="append", choices=(1, 2))
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    repeats = tuple(args.repeat) if args.repeat else (1, 2)
    result = render(
        args.plan, args.config, args.output, args.binary, args.model, args.codec,
        args.reference_wav, args.reference_text, args.device, args.passage,
        repeats, args.timeout,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
