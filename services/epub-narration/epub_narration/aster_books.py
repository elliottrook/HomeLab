"""Fail-closed consumer contract for the inactive Aster Books beta.

The consumer sees only atomic ready pointers. It does not scan work directories,
queue state, Calibre, or partially published generations.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
from typing import Callable, Optional

from .publication import SHA256, sha256_file, validate_generation


STEM = re.compile(r"^[0-9]{4}$")
MAX_POINTER_BYTES = 4096
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_CONTENT_BYTES = 8 * 1024 * 1024
MAX_TIMING_BYTES = 8 * 1024 * 1024


def _require(value: bool, code: str) -> None:
    if not value:
        raise ValueError(code)


def _regular(path: Path, limit: int, code: str) -> None:
    metadata = path.lstat()
    _require(stat.S_ISREG(metadata.st_mode) and not path.is_symlink(), code)
    _require(0 < metadata.st_size <= limit, code)


def _json(path: Path, limit: int, code: str):
    _regular(path, limit, code)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(code) from error


@dataclass(frozen=True)
class Cue:
    source_start: int
    source_end: int
    start_sample: int
    end_sample: int


@dataclass(frozen=True)
class BetaChapter:
    index: int
    text: str
    audio: Path
    audio_sha256: str
    sample_rate: int
    total_samples: int
    cues: tuple[Cue, ...]

    def cue_at(self, sample: int) -> Optional[Cue]:
        if isinstance(sample, bool) or not isinstance(sample, int) or sample < 0:
            return None
        return next((cue for cue in self.cues if cue.start_sample <= sample < cue.end_sample), None)


@dataclass(frozen=True)
class ReadyBook:
    book_id: int
    source_sha256: str
    manifest_sha256: str
    chapters: tuple[BetaChapter, ...]


def probe_opus(path: Path, sample_rate: int, total_samples: int) -> None:
    """Validate a bounded mono Opus stream and its exact decoded duration.

    Opus granule positions are always expressed at 48 kHz. The compiler's cue
    clock is 24 kHz, so the final granule minus pre-skip must be exactly twice
    the timing document's total sample count.
    """
    _regular(path, 1024 * 1024 * 1024, "beta-opus-file")
    raw = path.read_bytes()
    offset = 0
    serial = sequence = None
    last_granule = None
    header = b""
    eos = False
    while offset < len(raw):
        _require(offset + 27 <= len(raw) and raw[offset:offset + 4] == b"OggS"
                 and raw[offset + 4] == 0, "beta-opus-container")
        flags = raw[offset + 5]
        granule = struct.unpack_from("<Q", raw, offset + 6)[0]
        current_serial = struct.unpack_from("<I", raw, offset + 14)[0]
        current_sequence = struct.unpack_from("<I", raw, offset + 18)[0]
        segments = raw[offset + 26]
        _require(offset + 27 + segments <= len(raw), "beta-opus-container")
        lacing = raw[offset + 27:offset + 27 + segments]
        body_start = offset + 27 + segments
        body_end = body_start + sum(lacing)
        _require(body_end <= len(raw), "beta-opus-container")
        if serial is None:
            _require(flags & 0x02 and current_sequence == 0, "beta-opus-bos")
            serial, sequence = current_serial, 0
            header = raw[body_start:body_end]
        else:
            _require(current_serial == serial and current_sequence == sequence + 1,
                     "beta-opus-sequence")
            sequence = current_sequence
        if granule != 0xFFFFFFFFFFFFFFFF:
            last_granule = granule
        eos = bool(flags & 0x04)
        offset = body_end
    _require(offset == len(raw) and eos and len(header) >= 19 and header[:8] == b"OpusHead",
             "beta-opus-header")
    _require(header[8] == 1 and header[9] == 1 and sample_rate == 24_000,
             "beta-opus-format")
    pre_skip = struct.unpack_from("<H", header, 10)[0]
    input_rate = struct.unpack_from("<I", header, 12)[0]
    _require(input_rate == sample_rate and last_granule is not None
             and last_granule >= pre_skip
             and last_granule - pre_skip == total_samples * 2,
             "beta-opus-duration")


def load_ready_book(
    output_root: Path,
    book_id: int,
    probe: Optional[Callable[[Path, int, int], None]] = None,
) -> ReadyBook:
    """Load one complete generation through its atomic ready pointer only."""
    _require(type(book_id) is int and book_id > 0, "beta-book-id")
    root = output_root.resolve(strict=True)
    pointer_path = root / "ready" / f"{book_id}.json"
    pointer = _json(pointer_path, MAX_POINTER_BYTES, "beta-pointer")
    _require(type(pointer) is dict and set(pointer) == {
        "schema", "book_id", "source_sha256", "generation", "manifest_sha256"
    }, "beta-pointer-schema")
    _require(pointer["schema"] == 1 and pointer["book_id"] == book_id, "beta-pointer-identity")
    source_hash = pointer["source_sha256"]
    manifest_hash = pointer["manifest_sha256"]
    _require(isinstance(source_hash, str) and SHA256.fullmatch(source_hash), "beta-source-hash")
    _require(isinstance(manifest_hash, str) and SHA256.fullmatch(manifest_hash), "beta-manifest-hash")
    expected_relative = f"generations/{book_id}/{source_hash}"
    _require(pointer["generation"] == expected_relative, "beta-generation-path")
    generation = (root / expected_relative).resolve(strict=True)
    _require(generation == root / expected_relative, "beta-generation-path")
    manifest_path = generation / "manifest.json"
    _regular(manifest_path, MAX_MANIFEST_BYTES, "beta-manifest-file")
    _require(sha256_file(manifest_path) == manifest_hash, "beta-manifest-hash")
    manifest = validate_generation(generation)
    _require(manifest["book_id"] == book_id and manifest["source_sha256"] == source_hash,
             "beta-manifest-identity")

    records = {item["path"]: item for item in manifest["files"]}
    _require(len(records) == len(manifest["files"]), "beta-file-duplicate")
    groups: dict[str, set[str]] = {"chapters": set(), "timing": set(), "content": set()}
    for relative in records:
        parts = Path(relative).parts
        _require(len(parts) == 2 and parts[0] in groups, "beta-file-class")
        suffix = {"chapters": ".opus", "timing": ".json", "content": ".json"}[parts[0]]
        _require(Path(parts[1]).suffix == suffix and STEM.fullmatch(Path(parts[1]).stem) is not None,
                 "beta-file-name")
        groups[parts[0]].add(Path(parts[1]).stem)
    stems = groups["chapters"]
    _require(stems and stems == groups["timing"] == groups["content"], "beta-chapter-set")
    ordered = sorted(stems)
    _require(ordered == [f"{index:04d}" for index in range(1, len(ordered) + 1)],
             "beta-chapter-order")

    chapters: list[BetaChapter] = []
    for index, stem in enumerate(ordered, 1):
        content_path = generation / "content" / f"{stem}.json"
        timing_path = generation / "timing" / f"{stem}.json"
        audio_path = generation / "chapters" / f"{stem}.opus"
        content = _json(content_path, MAX_CONTENT_BYTES, "beta-content")
        timing = _json(timing_path, MAX_TIMING_BYTES, "beta-timing")
        _require(type(content) is dict and set(content) == {"schema", "chapter", "text", "text_sha256"},
                 "beta-content-schema")
        text = content["text"]
        _require(content["schema"] == 1 and content["chapter"] == index and isinstance(text, str) and text,
                 "beta-content-identity")
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        _require(content["text_sha256"] == text_hash, "beta-content-hash")
        _require(type(timing) is dict and set(timing) == {
            "schema", "timing_level", "sample_rate", "total_samples", "cleaned_text_sha256", "cues"
        }, "beta-timing-schema")
        sample_rate = timing["sample_rate"]
        total_samples = timing["total_samples"]
        _require(timing["schema"] == 1 and timing["timing_level"] == "sentence-sample-index"
                 and sample_rate == 24_000 and type(total_samples) is int and total_samples > 0
                 and timing["cleaned_text_sha256"] == text_hash, "beta-timing-identity")
        raw_cues = timing["cues"]
        _require(isinstance(raw_cues, list) and raw_cues, "beta-cues")
        cues: list[Cue] = []
        prior_source = prior_sample = 0
        for raw in raw_cues:
            _require(type(raw) is dict and set(raw) == {
                "source_start", "source_end", "start_sample", "end_sample", "spoken_sha256"
            }, "beta-cue-schema")
            source_start, source_end = raw["source_start"], raw["source_end"]
            start_sample, end_sample = raw["start_sample"], raw["end_sample"]
            _require(all(type(value) is int for value in (source_start, source_end, start_sample, end_sample)),
                     "beta-cue-type")
            _require(prior_source <= source_start < source_end <= len(text)
                     and prior_sample <= start_sample < end_sample <= total_samples,
                     "beta-cue-order")
            spoken_hash = hashlib.sha256(text[source_start:source_end].encode("utf-8")).hexdigest()
            _require(raw["spoken_sha256"] == spoken_hash, "beta-cue-text")
            cues.append(Cue(source_start, source_end, start_sample, end_sample))
            prior_source, prior_sample = source_end, end_sample
        if probe is not None:
            probe(audio_path, sample_rate, total_samples)
        chapters.append(BetaChapter(index, text, audio_path, records[f"chapters/{stem}.opus"]["sha256"],
                                    sample_rate, total_samples, tuple(cues)))
    return ReadyBook(book_id, source_hash, manifest_hash, tuple(chapters))


class ProgressStore:
    """Private atomic progress, keyed by the generation rather than a title."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, book: ReadyBook) -> Path:
        opaque = hashlib.sha256(f"{book.book_id}:{book.source_sha256}".encode()).hexdigest()
        return self.root / f"{opaque}.json"

    def _directory(self) -> None:
        if self.root.exists():
            metadata = self.root.lstat()
            _require(stat.S_ISDIR(metadata.st_mode) and not self.root.is_symlink(), "beta-progress-root")
        else:
            self.root.mkdir(mode=0o700, parents=True)
        os.chmod(self.root, 0o700)

    def load(self, book: ReadyBook) -> dict:
        self._directory()
        path = self._path(book)
        if not path.exists():
            return {"schema": 1, "source_sha256": book.source_sha256,
                    "chapter": 1, "sample": 0, "complete": False}
        value = _json(path, MAX_POINTER_BYTES, "beta-progress")
        _require(type(value) is dict and set(value) == {
            "schema", "source_sha256", "chapter", "sample", "complete"
        }, "beta-progress-schema")
        chapter = value["chapter"]
        sample = value["sample"]
        _require(value["schema"] == 1 and value["source_sha256"] == book.source_sha256
                 and type(chapter) is int and 1 <= chapter <= len(book.chapters)
                 and type(sample) is int and 0 <= sample <= book.chapters[chapter - 1].total_samples
                 and type(value["complete"]) is bool, "beta-progress-value")
        return value

    def save(self, book: ReadyBook, chapter: int, sample: int, complete: bool = False) -> dict:
        _require(type(chapter) is int and 1 <= chapter <= len(book.chapters), "beta-progress-chapter")
        limit = book.chapters[chapter - 1].total_samples
        _require(type(sample) is int and 0 <= sample <= limit and type(complete) is bool,
                 "beta-progress-sample")
        self._directory()
        value = {"schema": 1, "source_sha256": book.source_sha256,
                 "chapter": chapter, "sample": sample, "complete": complete}
        target = self._path(book)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.root,
                                         prefix=".position-", delete=False) as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            temporary = Path(stream.name)
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        return value


class BetaSession:
    """Deterministic transport model used by the inactive player adapter."""

    def __init__(self, book: ReadyBook, progress: ProgressStore) -> None:
        self.book = book
        self.progress = progress
        saved = progress.load(book)
        self.chapter = saved["chapter"]
        self.sample = saved["sample"]
        self.playing = False

    @property
    def current(self) -> BetaChapter:
        return self.book.chapters[self.chapter - 1]

    def play_pause(self) -> bool:
        self.playing = not self.playing
        if not self.playing:
            self.progress.save(self.book, self.chapter, self.sample)
        return self.playing

    def seek(self, sample: int) -> None:
        _require(type(sample) is int and 0 <= sample <= self.current.total_samples, "beta-seek")
        self.sample = sample

    def select_chapter(self, chapter: int) -> None:
        _require(type(chapter) is int and 1 <= chapter <= len(self.book.chapters), "beta-chapter")
        self.progress.save(self.book, self.chapter, self.sample)
        self.chapter, self.sample, self.playing = chapter, 0, False

    def highlight(self) -> Optional[tuple[int, int]]:
        cue = self.current.cue_at(self.sample)
        return None if cue is None else (cue.source_start, cue.source_end)

    def close(self) -> None:
        self.playing = False
        self.progress.save(self.book, self.chapter, self.sample)
