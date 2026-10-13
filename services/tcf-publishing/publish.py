"""Locked, human-confirmed publication pipeline for an approved edition."""

from __future__ import annotations

import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

from content import ContentError, SITES
import origin_sender
from release import prepare_release, verify_manifest


def candidate_relative(manifest: dict) -> Path:
    fingerprint = sha256(json.dumps(
        manifest["slots"], sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()[:12]
    return Path(manifest["site"]) / f"edition-{manifest['edition_id']}-{fingerprint}"


def _write_status(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(".next")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    os.replace(temporary, path)


def publish(store, site: str, confirmation: str, candidate_root: Path,
            release_root: Path, state_root: Path) -> dict:
    if site not in SITES:
        raise ContentError("unknown publication site")
    phrase = f"PUBLISH {site.upper()}"
    if confirmation != phrase:
        raise ContentError(f"publication confirmation must be {phrase}")
    state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = state_root / "publication.lock"
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ContentError("another publication is already running") from error
        manifest = store.edition_manifest(site)
        if not manifest["ready"]:
            raise ContentError("edition is incomplete")
        candidate = candidate_root / candidate_relative(manifest)
        if not candidate.is_dir():
            raise ContentError("build and review the private site preview first")
        verify_manifest(candidate)
        site_releases = release_root / site
        site_releases.mkdir(parents=True, exist_ok=True, mode=0o700)
        preparing = site_releases / f".edition-{manifest['edition_id']}-preparing"
        if preparing.exists():
            shutil.rmtree(preparing)
        metadata = prepare_release(candidate, preparing, site)
        release = site_releases / metadata["release_id"]
        if release.exists():
            existing_digest = verify_manifest(release)
            shutil.rmtree(preparing)
            if existing_digest != metadata["manifest_sha256"]:
                raise ContentError("existing immutable release differs")
        else:
            os.replace(preparing, release)
        status_path = state_root / f"{site}-publication.json"
        job = {**metadata, "state": "staging"}
        _write_status(status_path, job)
        try:
            origin_sender.stage(release, site, metadata["release_id"])
            _write_status(status_path, {**job, "state": "activating"})
            origin_sender.request("activate", site, metadata["release_id"],
                                  metadata["manifest_sha256"])
            result = store.record_publication(site, manifest["edition_id"],
                                              metadata["release_id"],
                                              metadata["manifest_sha256"])
            _write_status(status_path, {**result, "state": "published"})
            return result
        except Exception as error:
            _write_status(status_path, {**job, "state": "failed",
                                        "detail": type(error).__name__})
            if isinstance(error, ContentError):
                raise
            raise ContentError(
                "publication failed; the edition remains open and the recorded status must be reviewed"
            ) from error


def publication_status(store, site: str, state_root: Path) -> dict:
    if site not in SITES:
        raise ContentError("unknown publication site")
    origin = origin_sender.status().get(site)
    if not isinstance(origin, dict):
        raise ContentError("origin status omitted the selected site")
    state_path = state_root / f"{site}-publication.json"
    state = json.loads(state_path.read_text()) if state_path.is_file() else None
    return {"site": site, "latest": store.latest_publication(site),
            "last_rollback": store.latest_rollback(site), "origin": origin,
            "state": state,
            "rollback_available": origin.get("current") is not None
                                  and origin.get("previous") is not None}


def rollback(store, site: str, confirmation: str, state_root: Path) -> dict:
    if site not in SITES:
        raise ContentError("unknown rollback site")
    phrase = f"ROLLBACK {site.upper()}"
    if confirmation != phrase:
        raise ContentError(f"rollback confirmation must be {phrase}")
    state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = state_root / "publication.lock"
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ContentError("another publication is already running") from error
        origin = origin_sender.status().get(site)
        if not isinstance(origin, dict):
            raise ContentError("origin status omitted the selected site")
        current = origin.get("current")
        previous = origin.get("previous")
        if not isinstance(current, dict) or not isinstance(previous, dict):
            raise ContentError("no previous release is available for rollback")
        from_release = current.get("release_id")
        to_release = previous.get("release_id")
        digest = previous.get("manifest_sha256")
        if not all(isinstance(value, str) for value in (from_release, to_release, digest)):
            raise ContentError("origin rollback status is invalid")
        origin_sender.validate(site, from_release)
        origin_sender.validate(site, to_release)
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ContentError("origin rollback digest is invalid")
        status_path = state_root / f"{site}-publication.json"
        job = {"site": site, "state": "rolling-back",
               "from_release_id": from_release, "to_release_id": to_release,
               "manifest_sha256": digest}
        _write_status(status_path, job)
        try:
            origin_sender.request("rollback", site, to_release, digest)
            result = store.record_rollback(site, from_release, to_release, digest)
            _write_status(status_path, {**result, "state": "rolled-back"})
            return result
        except Exception as error:
            _write_status(status_path, {**job, "state": "rollback-failed",
                                        "detail": type(error).__name__})
            if isinstance(error, ContentError):
                raise
            raise ContentError(
                "rollback failed; inspect the recorded and origin status before retrying"
            ) from error
