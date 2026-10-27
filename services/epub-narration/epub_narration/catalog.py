"""Read the minimum Calibre catalogue surface without write authority."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import sqlite3
from urllib.parse import quote


@dataclass(frozen=True)
class EpubSource:
    calibre_id: int
    path: Path


@dataclass(frozen=True)
class SourceFingerprint:
    calibre_id: int
    source_sha256: str
    size: int
    mtime_ns: int


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def read_epub_sources(database: Path, library_root: Path) -> tuple[EpubSource, ...]:
    """Return only EPUB locations from a Calibre database opened read-only."""
    database = database.resolve(strict=True)
    library_root = library_root.resolve(strict=True)
    uri = f"file:{quote(str(database))}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute(
            "SELECT b.id, b.path, d.name "
            "FROM books AS b JOIN data AS d ON d.book = b.id "
            "WHERE upper(d.format) = 'EPUB' ORDER BY b.id, d.id"
        ).fetchall()
    finally:
        connection.close()

    found: list[EpubSource] = []
    seen: set[int] = set()
    for book_id, relative_directory, basename in rows:
        if not isinstance(book_id, int) or book_id < 1 or book_id in seen:
            raise ValueError("calibre-epub-identity")
        if not isinstance(relative_directory, str) or not isinstance(basename, str):
            raise ValueError("calibre-epub-path")
        filename = basename if basename.lower().endswith(".epub") else basename + ".epub"
        candidate = (library_root / relative_directory / filename).resolve(strict=True)
        if not _contained(library_root, candidate) or candidate.suffix.lower() != ".epub":
            raise ValueError("calibre-epub-path")
        if not candidate.is_file():
            raise ValueError("calibre-epub-file")
        found.append(EpubSource(book_id, candidate))
        seen.add(book_id)
    return tuple(found)


def fingerprint(source: EpubSource, block_size: int = 1024 * 1024) -> SourceFingerprint:
    """Hash a source only when its identity and stat values remain stable."""
    before = source.path.stat()
    digest = hashlib.sha256()
    with source.path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    after = source.path.stat()
    stable = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) == (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if not stable:
        raise ValueError("source-changed")
    return SourceFingerprint(source.calibre_id, digest.hexdigest(), after.st_size, after.st_mtime_ns)

