"""Content-silent reconciliation of Calibre EPUBs into the durable queue."""

from __future__ import annotations

from pathlib import Path

from .catalog import fingerprint, read_epub_sources
from .runtime import atomic_private_json, exclusive_lock, status_payload
from .state import QueueStore


def reconcile_catalogue(
    *,
    database: Path,
    library_root: Path,
    state_root: Path,
    compiler_contract: str,
) -> dict:
    store = QueueStore(state_root / "queue.db")
    store.initialize()
    with exclusive_lock(state_root / "monitor.lock"):
        sources = read_epub_sources(database, library_root)
        fingerprints = tuple(fingerprint(source) for source in sources)
        inserted = store.reconcile(fingerprints, compiler_contract)
        counts = store.counts(compiler_contract)
        payload = status_payload(
            state="healthy",
            counts=counts,
            oldest_queued_age=store.oldest_queued_age(compiler_contract),
        )
        payload["source_count"] = len(fingerprints)
        payload["queued_new_count"] = inserted
        atomic_private_json(state_root / "monitor-status.json", payload)
        return payload
