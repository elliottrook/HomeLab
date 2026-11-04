#!/usr/bin/env python3
"""Run one private canonical-voice probe through the OpenVINO plugin EP."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import wave

import numpy as np


MODEL_SHA256 = "f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96"
VOICE = "bm_daniel"
LANGUAGE = "en-gb"
SPEED = 0.95
SAMPLE_RATE = 24_000
WORD = re.compile(r"\b[^\W_]+(?:['’][^\W_]+)?\b", re.UNICODE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def write_pcm16(path: Path, audio: np.ndarray) -> None:
    pcm = np.rint(np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())
    os.chmod(path, 0o600)


def select_device(ort, plugin, requested: str):
    ep_name = plugin.get_ep_name()
    devices = [
        device
        for device in ort.get_ep_devices()
        if device.ep_name == ep_name
        and device.ep_metadata.get("ov_device") == requested
    ]
    if len(devices) != 1:
        available = sorted(
            str(device.ep_metadata.get("ov_device"))
            for device in ort.get_ep_devices()
            if device.ep_name == ep_name
        )
        raise RuntimeError(f"openvino-device:{requested}:available={available}")
    return devices[0]


def run(args: argparse.Namespace) -> dict:
    if sha256_file(args.model) != MODEL_SHA256:
        raise RuntimeError("probe-model-hash")
    text = args.text.read_text(encoding="utf-8").strip()
    word_count = len(WORD.findall(text))
    if word_count < 50:
        raise RuntimeError("probe-text-too-short")

    import onnxruntime as ort
    from kokoro_onnx import Kokoro

    plugin_registered = False
    engine = None
    session = None
    try:
        compile_started = time.monotonic()
        if args.legacy:
            session = ort.InferenceSession(
                str(args.model),
                providers=[(
                    "OpenVINOExecutionProvider",
                    {"device_type": args.device, "precision": "ACCURACY"},
                )],
            )
            backend = "onnxruntime-openvino-legacy"
        else:
            import onnxruntime_ep_openvino as openvino_ep

            ort.register_execution_provider_library(
                "openvino_ep", openvino_ep.get_library_path()
            )
            plugin_registered = True
            device = select_device(ort, openvino_ep, args.device)
            session_options = ort.SessionOptions()
            config = {
                args.device: {
                    "EXECUTION_MODE_HINT": "ACCURACY",
                    "PERFORMANCE_HINT": "LATENCY",
                }
            }
            session_options.add_provider_for_devices(
                [device], {"load_config": json.dumps(config)}
            )
            session = ort.InferenceSession(
                str(args.model), sess_options=session_options
            )
            backend = "onnxruntime-openvino-plugin"
        compile_seconds = time.monotonic() - compile_started
        active_providers = session.get_providers()
        if "OpenVINOExecutionProvider" not in active_providers:
            raise RuntimeError(
                f"openvino-provider-fallback:active={active_providers}"
            )

        engine = Kokoro.__new__(Kokoro)
        engine._setup(
            session=session,
            model_path=str(args.model),
            voices_path=str(args.voices),
            espeak_config=None,
            vocab_config=None,
        )
        render_started = time.monotonic()
        audio, sample_rate = engine.create(
            text,
            voice=VOICE,
            speed=SPEED,
            lang=LANGUAGE,
        )
        render_seconds = time.monotonic() - render_started
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if sample_rate != SAMPLE_RATE or len(audio) < 1 or not np.isfinite(audio).all():
            raise RuntimeError("probe-audio-format")
        audio_seconds = len(audio) / SAMPLE_RATE
        words_per_minute = word_count * 60.0 / audio_seconds
        write_pcm16(args.output, audio)
        result = {
            "schema": 1,
            "backend": backend,
            "device": args.device,
            "active_providers": active_providers,
            "model_sha256": MODEL_SHA256,
            "voices_sha256": sha256_file(args.voices),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "word_count": word_count,
            "sample_rate": sample_rate,
            "samples": len(audio),
            "audio_seconds": audio_seconds,
            "compile_seconds": compile_seconds,
            "render_seconds": render_seconds,
            "render_factor": render_seconds / audio_seconds,
            "words_per_minute": words_per_minute,
            "pacing_valid": 120.0 <= words_per_minute <= 240.0,
            "wav_sha256": sha256_file(args.output),
            "onnxruntime_version": ort.__version__,
        }
        args.result.write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        os.chmod(args.result, 0o600)
        return result
    finally:
        if engine is not None:
            engine.voices.close()
        del engine
        del session
        gc.collect()
        if plugin_registered:
            ort.unregister_execution_provider_library("openvino_ep")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--voices", required=True, type=Path)
    parser.add_argument("--text", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--device", default="GPU")
    parser.add_argument("--legacy", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    result = run(args)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pacing_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
