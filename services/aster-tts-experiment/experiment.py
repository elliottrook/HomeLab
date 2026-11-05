#!/usr/bin/env python3
"""Prepare, validate and blind the bounded Aster TTS listening experiment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time
import wave


CORPUS_SCHEMA = "aster-tts-pronunciation-corpus.v1"
PLAN_SCHEMA = "aster-tts-experiment-plan.v1"
REPORT_SCHEMA = "aster-tts-render-report.v1"
BLIND_SCHEMA = "aster-tts-blind-package.v1"
SAMPLE_RATE = 24_000
REPEATS = (1, 2)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def load_corpus(path: Path) -> dict:
    corpus = _read_json(path)
    passages = corpus.get("passages")
    if corpus.get("schema") != CORPUS_SCHEMA or corpus.get("language") != "en-CA":
        raise ValueError("unsupported corpus contract")
    if not isinstance(passages, list) or len(passages) != 6:
        raise ValueError("the experiment requires exactly six passages")
    identifiers: set[str] = set()
    for passage in passages:
        if not isinstance(passage, dict):
            raise ValueError("passage must be an object")
        identifier = passage.get("id")
        text = passage.get("text")
        if (not isinstance(identifier, str) or not identifier.replace("_", "").isalnum()
                or identifier in identifiers):
            raise ValueError("passage IDs must be unique and path-safe")
        identifiers.add(identifier)
        if passage.get("source_class") not in {"public", "synthetic"}:
            raise ValueError("private text is forbidden in the fixed corpus")
        if not isinstance(text, str) or not 40 <= len(text) <= 2_000:
            raise ValueError("passage text length is outside the production contract")
        if not isinstance(passage.get("targets"), list) or not passage["targets"]:
            raise ValueError("every passage requires pronunciation targets")
    return corpus


def _load_voice_contract(path: Path):
    if not path.is_file() or path.is_symlink():
        raise ValueError("voice contract must be a regular file")
    spec = importlib.util.spec_from_file_location("aster_experiment_voice_contract", path)
    if spec is None or spec.loader is None:
        raise ValueError("unable to load voice contract")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
        sys.modules.pop(spec.name, None)
    for name in ("normalize_for_speech", "semantic_units"):
        if not callable(getattr(module, name, None)):
            raise ValueError(f"voice contract is missing {name}")
    return module


def prepare(corpus_path: Path, voice_contract: Path, output: Path) -> dict:
    corpus = load_corpus(corpus_path)
    contract = _load_voice_contract(voice_contract)
    passages = []
    for source in corpus["passages"]:
        normalized = contract.normalize_for_speech(source["text"])
        units = contract.semantic_units(normalized)
        if not units or any(not unit or len(unit) > 240 for unit in units):
            raise ValueError(f"invalid production units for {source['id']}")
        passages.append({
            **source,
            "source_sha256": hashlib.sha256(source["text"].encode()).hexdigest(),
            "normalized_text": normalized,
            "normalized_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
            "units": units,
            "unit_sha256": [hashlib.sha256(unit.encode()).hexdigest() for unit in units],
        })
    plan = {
        "schema": PLAN_SCHEMA,
        "corpus_sha256": sha256_file(corpus_path),
        "voice_contract_sha256": sha256_file(voice_contract),
        "voice_contract_name": voice_contract.name,
        "language": corpus["language"],
        "repeats": list(REPEATS),
        "passages": passages,
    }
    _atomic_json(output, plan)
    return plan


def inspect_wav(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing regular WAV: {path}")
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels() != 1 or audio.getsampwidth() != 2
                or audio.getframerate() != SAMPLE_RATE or audio.getcomptype() != "NONE"):
            raise ValueError(f"WAV contract mismatch: {path}")
        frames = audio.getnframes()
    if frames <= 0:
        raise ValueError(f"empty WAV: {path}")
    return {
        "bytes": path.stat().st_size,
        "frames": frames,
        "audio_seconds": round(frames / SAMPLE_RATE, 6),
        "sha256": sha256_file(path),
    }


def record(plan_path: Path, render_dir: Path, config_path: Path, output: Path) -> dict:
    plan = _read_json(plan_path)
    config = _read_json(config_path)
    if plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("invalid experiment plan")
    required = {"id", "engine", "model", "backend", "seed", "artifact_pins"}
    if not required.issubset(config) or not isinstance(config["artifact_pins"], dict):
        raise ValueError("incomplete renderer configuration")
    results = []
    for passage in plan["passages"]:
        words = len(passage["normalized_text"].split())
        for repeat in REPEATS:
            stem = f"{passage['id']}-r{repeat}"
            measured = inspect_wav(render_dir / f"{stem}.wav")
            timing_path = render_dir / f"{stem}.timing.json"
            timing = _read_json(timing_path)
            render_seconds = timing.get("render_seconds")
            if (timing.get("schema") != "aster-tts-render-timing.v1"
                    or not isinstance(render_seconds, (int, float)) or render_seconds <= 0):
                raise ValueError(f"invalid timing evidence: {timing_path}")
            wpm = words * 60 / measured["audio_seconds"]
            if not 90 <= wpm <= 260:
                raise ValueError(f"implausible speech rate for {stem}: {wpm:.2f}")
            results.append({
                "passage_id": passage["id"],
                "repeat": repeat,
                "wav": f"{stem}.wav",
                **measured,
                "render_seconds": round(float(render_seconds), 6),
                "real_time_factor": round(float(render_seconds) / measured["audio_seconds"], 6),
                "words_per_minute": round(wpm, 6),
                "timing_sha256": sha256_file(timing_path),
            })
    report = {
        "schema": REPORT_SCHEMA,
        "plan_sha256": sha256_file(plan_path),
        "config": config,
        "result_count": len(results),
        "results": results,
    }
    _atomic_json(output, report)
    return report


def _normalize_audio(source: Path, destination: Path) -> None:
    result = subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(source),
        "-map_metadata", "-1", "-af", "loudnorm=I=-18:TP=-2:LRA=11",
        "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s16le", str(destination),
    ], capture_output=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError("blind loudness normalization failed")


def blind(plan_path: Path, reports: list[Path], output: Path, seed: int) -> dict:
    if output.exists():
        raise FileExistsError("blind output already exists")
    plan_sha = sha256_file(plan_path)
    loaded = [_read_json(path) for path in reports]
    if len(loaded) < 2 or len({item["config"]["id"] for item in loaded}) != len(loaded):
        raise ValueError("at least two unique renderer reports are required")
    for item in loaded:
        if item.get("schema") != REPORT_SCHEMA or item.get("plan_sha256") != plan_sha:
            raise ValueError("renderer report does not match the plan")
    output.mkdir(parents=True, mode=0o700)
    audio_root = output / "audio"
    audio_root.mkdir(mode=0o700)
    rng = random.Random(seed)
    public_items = []
    private_mapping = []
    for result_index in range(len(loaded[0]["results"])):
        candidates = list(range(len(loaded)))
        rng.shuffle(candidates)
        base = loaded[0]["results"][result_index]
        sample_id = f"{base['passage_id']}-r{base['repeat']}"
        for label_index, candidate_index in enumerate(candidates):
            label = chr(ord("A") + label_index)
            report = loaded[candidate_index]
            result = report["results"][result_index]
            if (result["passage_id"], result["repeat"]) != (base["passage_id"], base["repeat"]):
                raise ValueError("renderer result ordering mismatch")
            report_path = reports[candidate_index]
            source = report_path.parent / result["wav"]
            if sha256_file(source) != result["sha256"]:
                raise ValueError("renderer WAV hash mismatch")
            destination = audio_root / f"{sample_id}-{label}.wav"
            _normalize_audio(source, destination)
            public_items.append({"sample": sample_id, "label": label,
                                 "wav": str(destination.relative_to(output))})
            private_mapping.append({"sample": sample_id, "label": label,
                                    "config_id": report["config"]["id"],
                                    "source_sha256": result["sha256"],
                                    "blind_sha256": sha256_file(destination)})
    package = {"schema": BLIND_SCHEMA, "plan_sha256": plan_sha,
               "created_epoch": int(time.time()), "items": public_items}
    mapping = {"schema": f"{BLIND_SCHEMA}-mapping", "seed": seed,
               "items": private_mapping}
    _atomic_json(output / "playlist.json", package)
    _atomic_json(output / "PRIVATE-mapping.json", mapping)
    return package


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate-corpus")
    validate_parser.add_argument("--corpus", type=Path, required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--corpus", type=Path, required=True)
    prepare_parser.add_argument("--voice-contract", type=Path, required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--plan", type=Path, required=True)
    record_parser.add_argument("--render-dir", type=Path, required=True)
    record_parser.add_argument("--config", type=Path, required=True)
    record_parser.add_argument("--output", type=Path, required=True)
    blind_parser = subparsers.add_parser("blind")
    blind_parser.add_argument("--plan", type=Path, required=True)
    blind_parser.add_argument("--report", type=Path, action="append", required=True)
    blind_parser.add_argument("--output", type=Path, required=True)
    blind_parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    if args.command == "validate-corpus":
        result = load_corpus(args.corpus)
    elif args.command == "prepare":
        result = prepare(args.corpus, args.voice_contract, args.output)
    elif args.command == "record":
        result = record(args.plan, args.render_dir, args.config, args.output)
    else:
        result = blind(args.plan, args.report, args.output, args.seed)
    print(json.dumps({"state": "ok", "schema": result["schema"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
