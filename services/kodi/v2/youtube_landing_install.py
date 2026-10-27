"""Exact reversible installer for the HP Aster YouTube landing."""

import hashlib
import json
from pathlib import Path
import re

from digest_news_install import atomic


CHECKPOINT = ".aster-checkpoints/aster-youtube-search6-20261027"
HELPERS = {"youtube_landing_install.py", "deploy_youtube_landing.py",
           "digest_news_install.py"}
TARGETS = {
    ".kodi/addons/skin.asterhome/1080i/Includes.xml",
    ".kodi/addons/skin.asterhome/1080i/MyVideoNav.xml",
}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unlinked(path):
    path = Path(path)
    require(not any(node.is_symlink() for node in (path, *path.parents)),
            "youtube-landing-linked-path")


def inspect(stage, pin):
    stage = Path(stage)
    require(re.fullmatch("[0-9a-f]{64}", pin or "") is not None,
            "youtube-landing-pin-format")
    require(sha(stage / "manifest.json") == pin,
            "youtube-landing-manifest-pin")
    manifest = json.loads((stage / "manifest.json").read_text())
    rows = manifest.get("files", [])
    require(manifest.get("schema") == 1
            and manifest.get("kind") == "hp-aster-youtube-landing.v2"
            and manifest.get("official_addon") == "plugin.video.youtube"
            and manifest.get("credential_files") == 0
            and manifest.get("production_changed") is False
            and {row.get("path") for row in rows} == TARGETS
            and len(rows) == 2, "youtube-landing-contract")
    require(set(manifest.get("helpers", {})) == HELPERS,
            "youtube-landing-helper-contract")
    for name, digest in manifest["helpers"].items():
        require(sha(stage / name) == digest,
                "youtube-landing-helper-drift")
    for row in rows:
        require(set(row) == {"path", "bytes", "sha256", "before_sha256"}
                and re.fullmatch("[0-9a-f]{64}", row["sha256"])
                and re.fullmatch("[0-9a-f]{64}", row["before_sha256"]),
                "youtube-landing-row")
        payload = stage / "payload" / row["path"]
        unlinked(payload)
        require(payload.is_file() and payload.stat().st_size == row["bytes"]
                and sha(payload) == row["sha256"],
                "youtube-landing-payload-drift")
    return manifest


def state(stage, storage, pin):
    manifest = inspect(stage, pin)
    checkpoint = Path(storage) / CHECKPOINT
    require(checkpoint.is_dir()
            and sha(checkpoint / "manifest.json") == pin,
            "youtube-landing-checkpoint")
    value = json.loads((checkpoint / "state.json").read_text()).get("state")
    require(value in ("prepared", "installed", "rolled_back"),
            "youtube-landing-state")
    for row in manifest["files"]:
        require(sha(checkpoint / "original" / row["path"])
                == row["before_sha256"], "youtube-landing-recovery-drift")
    return manifest, value


def active(stage, storage, pin):
    manifest, value = state(stage, storage, pin)
    enabled = value == "installed"
    for row in manifest["files"]:
        expected = row["sha256"] if enabled else row["before_sha256"]
        require(sha(Path(storage) / row["path"]) == expected,
                "youtube-landing-active-drift")
    return enabled


def restore(manifest, storage, checkpoint):
    for row in manifest["files"]:
        target = Path(storage) / row["path"]
        require(sha(target) in {row["sha256"], row["before_sha256"]},
                "youtube-landing-rollback-drift")
        atomic(target, (checkpoint / "original" / row["path"]).read_bytes())


def run(mode, stage, storage, pin, *, idle):
    require(mode in ("install", "verify", "rollback"),
            "youtube-landing-mode")
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, pin)
    require(idle(), "youtube-landing-home-idle-required")
    checkpoint = storage / CHECKPOINT
    if mode == "verify":
        return {"verified": True, "active": active(stage, storage, pin),
                "files": 2, "credential_files": 0}
    if mode == "rollback":
        _, value = state(stage, storage, pin)
        require(value == "installed", "youtube-landing-not-active")
        restore(manifest, storage, checkpoint)
        atomic(checkpoint / "state.json", b'{"state":"rolled_back"}\n')
        require(not active(stage, storage, pin),
                "youtube-landing-rollback-failed")
        return {"rolled_back": True, "files": 2, "credential_files": 0}
    require(not checkpoint.exists(), "youtube-landing-checkpoint-exists")
    for row in manifest["files"]:
        target = storage / row["path"]
        unlinked(target)
        require(target.is_file() and sha(target) == row["before_sha256"],
                "youtube-landing-exact-predecessor")
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint / "manifest.json", (stage / "manifest.json").read_bytes())
    for row in manifest["files"]:
        atomic(checkpoint / "original" / row["path"],
               (storage / row["path"]).read_bytes())
    atomic(checkpoint / "state.json", b'{"state":"prepared"}\n')
    try:
        require(idle(), "youtube-landing-home-idle-required")
        for row in manifest["files"]:
            atomic(storage / row["path"],
                   (stage / "payload" / row["path"]).read_bytes())
        atomic(checkpoint / "state.json", b'{"state":"installed"}\n')
        require(active(stage, storage, pin),
                "youtube-landing-install-failed")
    except Exception:
        restore(manifest, storage, checkpoint)
        atomic(checkpoint / "state.json", b'{"state":"rolled_back"}\n')
        raise
    return {"installed": True, "files": 2, "checkpoint_verified": True,
            "credential_files": 0}
