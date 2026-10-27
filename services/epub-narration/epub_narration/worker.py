"""Single-concurrency private EPUB narration compiler worker."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil

from . import COMPILER_CONTRACT
from .catalog import EpubSource, fingerprint, read_epub_sources
from .epub import extract_chapters
from .publication import VOICE, publish_generation
from .renderer import CLEANUP_SHA256, KokoroChapterRenderer, RenderFailure
from .runtime import atomic_private_json, exclusive_lock, status_payload
from .state import QueueStore


PARSER_CONTRACT = "bounded-epub-spine-v1"
ENCODER_CONTRACT = "ffmpeg-libopus-48k-v1"
MINIMUM_FREE_BYTES = 1024 * 1024 * 1024


@dataclass(frozen=True)
class WorkerConfig:
    database: Path
    library_root: Path
    data_root: Path
    model: Path
    voices: Path
    cleanup: Path
    compiler_contract: str = COMPILER_CONTRACT
    max_attempts: int = 3
    minimum_free_bytes: int = MINIMUM_FREE_BYTES

    @property
    def state_root(self) -> Path:
        return self.data_root / "state"


def _source_for_book(config: WorkerConfig, book_id: int) -> EpubSource:
    found = [source for source in read_epub_sources(config.database, config.library_root) if source.calibre_id == book_id]
    if len(found) != 1:
        raise RenderFailure("source-changed")
    return found[0]


def _manifest(config: WorkerConfig, *, book_id: int, source_sha256: str, files: list[dict]) -> dict:
    return {
        "schema": 1,
        "state": "ready-candidate",
        "contracts": {
            "compiler": config.compiler_contract,
            "parser": PARSER_CONTRACT,
            "cleanup": f"sha256:{CLEANUP_SHA256}",
            "encoder": ENCODER_CONTRACT,
        },
        "book_id": book_id,
        "source_sha256": source_sha256,
        "voice": VOICE,
        "timing_level": "sentence-sample-index",
        "sample_rate": 24_000,
        "codec": {"name": "opus", "bitrate": 48000, "channels": 1},
        "files": files,
    }


def _failure_code(error: BaseException) -> str:
    if isinstance(error, RenderFailure) and str(error) in {
        "source-changed", "voice-contract", "timing-invalid", "quota"
    }:
        return str(error)
    if isinstance(error, (ValueError, OSError)):
        return "epub-invalid"
    return "publish"


def run_once(config: WorkerConfig, renderer_factory=KokoroChapterRenderer) -> dict:
    config.data_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    store = QueueStore(config.state_root / "queue.db")
    store.initialize()
    with exclusive_lock(config.state_root / "worker.lock"):
        for attempt_id in store.recover_interrupted(config.compiler_contract, config.max_attempts):
            interrupted = config.data_root / "work" / attempt_id
            if interrupted.is_dir():
                shutil.rmtree(interrupted)
        record = store.claim_next(config.compiler_contract, config.max_attempts)
        if record is None:
            payload = status_payload(
                state="idle",
                counts=store.counts(config.compiler_contract),
                oldest_queued_age=store.oldest_queued_age(config.compiler_contract),
            )
            atomic_private_json(config.state_root / "worker-status.json", payload)
            return payload
        assert record.attempt_id is not None
        staging = config.data_root / "work" / record.attempt_id
        staging.mkdir(parents=True, mode=0o700)
        renderer = None
        try:
            free = shutil.disk_usage(config.data_root).free
            if free < config.minimum_free_bytes:
                raise RenderFailure("quota")
            source = _source_for_book(config, record.book_id)
            current = fingerprint(source)
            if (
                current.source_sha256 != record.source_sha256
                or current.size != record.source_size
                or current.mtime_ns != record.source_mtime_ns
            ):
                raise RenderFailure("source-changed")
            chapters = extract_chapters(source.path)
            store.transition(record.book_id, record.source_sha256, config.compiler_contract, "narrating")
            renderer = renderer_factory(model=config.model, voices=config.voices, cleanup=config.cleanup)
            files = renderer.render(chapters, staging)
            store.transition(record.book_id, record.source_sha256, config.compiler_contract, "aligning")
            manifest_path = staging / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    _manifest(
                        config,
                        book_id=record.book_id,
                        source_sha256=record.source_sha256,
                        files=files,
                    ),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            os.chmod(manifest_path, 0o600)
            publish_generation(staging, config.data_root)
            store.transition(record.book_id, record.source_sha256, config.compiler_contract, "ready")
            state = "healthy"
        except BaseException as error:
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            code = _failure_code(error)
            current_state = store.state(record.book_id, record.source_sha256, config.compiler_contract)
            if current_state not in {"failed", "ready"}:
                store.transition(
                    record.book_id,
                    record.source_sha256,
                    config.compiler_contract,
                    "failed",
                    code,
                )
            failure_path = config.data_root / "failed" / f"{record.attempt_id}.json"
            atomic_private_json(failure_path, {"schema": 1, "failure_code": code})
            state = "failed"
        finally:
            if renderer is not None:
                renderer.close()
            if staging.is_dir():
                shutil.rmtree(staging)
        payload = status_payload(
            state=state,
            counts=store.counts(config.compiler_contract),
            oldest_queued_age=store.oldest_queued_age(config.compiler_contract),
        )
        atomic_private_json(config.state_root / "worker-status.json", payload)
        return payload
