"""Pinned, persistent Kokoro renderer pool for the M2 candidate."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

EXPECTED_MODEL_SHA256 = "f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96"
EXPECTED_VOICES_SHA256 = "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"

MODEL_PATH = Path(os.environ.get(
    "ASTER_VOICE_KOKORO_MODEL", "/opt/aster-voice/models/kokoro-v1.0.fp16.onnx"
))
VOICES_PATH = Path(os.environ.get(
    "ASTER_VOICE_KOKORO_VOICES", "/opt/aster-voice/models/voices-v1.0.bin"
))
VOICE = os.environ.get("ASTER_VOICE_NAME", "bm_daniel")
LANGUAGE = os.environ.get("ASTER_VOICE_LANGUAGE", "en-gb")
SPEED = float(os.environ.get("ASTER_VOICE_SPEED", "0.95"))
INTRA_OP_THREADS = int(os.environ.get("ASTER_VOICE_INTRA_OP_THREADS", "2"))
INTER_OP_THREADS = int(os.environ.get("ASTER_VOICE_INTER_OP_THREADS", "1"))
ACKNOWLEDGEMENT = "There, that's done."


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_assets(model: Path = MODEL_PATH, voices: Path = VOICES_PATH) -> None:
    expected = ((model, EXPECTED_MODEL_SHA256), (voices, EXPECTED_VOICES_SHA256))
    for path, checksum in expected:
        if not path.is_file():
            raise RuntimeError(f"required Kokoro asset is missing: {path}")
        if sha256(path) != checksum:
            raise RuntimeError(f"Kokoro asset digest mismatch: {path.name}")


class KokoroWorker:
    """One engine/session, called serially by exactly one scheduler worker."""

    def __init__(self, model: Path = MODEL_PATH, voices: Path = VOICES_PATH):
        import onnxruntime as ort
        from kokoro_onnx import Kokoro
        from kokoro_onnx.session import resolve_providers

        options = ort.SessionOptions()
        options.intra_op_num_threads = INTRA_OP_THREADS
        options.inter_op_num_threads = INTER_OP_THREADS
        session = ort.InferenceSession(
            str(model), sess_options=options, providers=resolve_providers()
        )
        engine = Kokoro.__new__(Kokoro)
        engine._setup(
            session=session,
            model_path=str(model),
            voices_path=str(voices),
            espeak_config=None,
            vocab_config=None,
        )
        self._engine: Any = engine

    def render(self, text: str) -> tuple[bytes, int]:
        import numpy as np

        audio, sample_rate = self._engine.create(
            text, voice=VOICE, speed=SPEED, lang=LANGUAGE
        )
        samples = np.clip(audio, -1.0, 1.0)
        pcm = (samples * 32767.0).astype("<i2", copy=False).tobytes()
        return pcm, int(sample_rate)

    def close(self) -> None:
        self._engine.voices.close()


class KokoroRendererPool:
    """The approved topology: two engines, two threads each, one inter-op."""

    def __init__(self, model: Path = MODEL_PATH, voices: Path = VOICES_PATH):
        verify_assets(model, voices)
        self.workers = (KokoroWorker(model, voices), KokoroWorker(model, voices))
        # This exact phrase passed Jason's listening gate. It is deterministic
        # and may be returned only after the caller reports action success.
        self._cache = {ACKNOWLEDGEMENT: self.workers[0].render(ACKNOWLEDGEMENT)}

    def _render(self, worker_index: int, text: str) -> tuple[bytes, int]:
        cached = self._cache.get(text)
        if cached is not None:
            return cached
        return self.workers[worker_index].render(text)

    @property
    def renderers(self):
        return (
            lambda text: self._render(0, text),
            lambda text: self._render(1, text),
        )

    def close(self) -> None:
        for worker in self.workers:
            worker.close()

    def healthy(self) -> bool:
        return True
