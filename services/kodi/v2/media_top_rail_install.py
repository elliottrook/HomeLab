"""Exact reversible installer for the HP Media top-rail correction."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


HOME = Path(".kodi/addons/skin.asterhome/1080i/Home.xml")
PARENT = Path(".aster-checkpoints/aster-acquisition-label9/manifest.json")
PARENT_STATE = Path(".aster-checkpoints/aster-acquisition-label9/state.json")
PARENT_SHA = "3edb117155442a8d9a035478c019fd6eaf9ae2ad63971bac7d09c2905d8b8930"
CHECKPOINT = Path(".aster-checkpoints/aster-media-top-rail1")


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)),
            "media-top-rail-linked-path")


def atomic(path, raw, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".media-top-rail.",
                                              dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def inspect(stage, pin):
    stage = Path(stage)
    require(re.fullmatch("[0-9a-f]{64}", pin or "") is not None,
            "media-top-rail-pin-format")
    require(sha(stage / "manifest.json") == pin,
            "media-top-rail-manifest-pin")
    manifest = json.loads((stage / "manifest.json").read_text())
    require(manifest.get("schema") == 1
            and manifest.get("kind") == "hp-media-top-rail.v2"
            and manifest.get("parent_manifest_sha256") == PARENT_SHA
            and set(manifest) == {"schema", "kind", "parent_manifest_sha256",
                                  "file", "helper_sha256",
                                  "deploy_sha256"},
            "media-top-rail-contract")
    row = manifest.get("file", {})
    require(row.get("path") == HOME.as_posix()
            and re.fullmatch("[0-9a-f]{64}", row.get("before_sha256", ""))
            and re.fullmatch("[0-9a-f]{64}", row.get("sha256", "")),
            "media-top-rail-shape")
    payload = stage / "payload" / HOME
    helper = stage / "media_top_rail_install.py"
    deploy = stage / "deploy_media_top_rail.py"
    safe(payload); safe(helper); safe(deploy)
    require(payload.is_file() and payload.stat().st_size == row.get("bytes")
            and sha(payload) == row["sha256"]
            and helper.is_file() and sha(helper) == manifest["helper_sha256"]
            and deploy.is_file() and sha(deploy) == manifest["deploy_sha256"],
            "media-top-rail-payload-drift")
    return manifest


def run(mode, stage, storage, pin, *, stopped):
    require(mode in ("install", "verify", "rollback"),
            "media-top-rail-mode")
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, pin); row = manifest["file"]
    require((storage / PARENT).is_file()
            and sha(storage / PARENT) == PARENT_SHA
            and json.loads((storage / PARENT_STATE).read_text()).get("state")
            == "installed", "media-top-rail-parent-drift")
    target = storage / HOME; checkpoint = storage / CHECKPOINT
    if mode == "verify":
        require(checkpoint.is_dir(), "media-top-rail-checkpoint-missing")
        state = json.loads((checkpoint / "state.json").read_text()).get("state")
        require(state in ("installed", "rolled_back"),
                "media-top-rail-state")
        require(target.is_file() and sha(target) == row[
            "sha256" if state == "installed" else "before_sha256"],
                "media-top-rail-active-drift")
        return {"verified": True, "active": state == "installed"}
    require(stopped(), "media-top-rail-stop-kodi-first")
    if mode == "rollback":
        require(checkpoint.is_dir()
                and json.loads((checkpoint / "state.json").read_text()).get("state")
                == "installed" and sha(target) == row["sha256"],
                "media-top-rail-not-active")
        original = checkpoint / "original" / HOME
        require(original.is_file() and sha(original) == row["before_sha256"],
                "media-top-rail-recovery-drift")
        atomic(target, original.read_bytes(), 0o644)
        atomic(checkpoint / "state.json", b'{"state":"rolled_back"}\n')
        return {"rolled_back": True, "recovery_retained": True}
    require(not checkpoint.exists() and target.is_file()
            and sha(target) == row["before_sha256"],
            "media-top-rail-exact-predecessor")
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint / "manifest.json", (stage / "manifest.json").read_bytes())
    atomic(checkpoint / "original" / HOME, target.read_bytes())
    atomic(checkpoint / "state.json", b'{"state":"prepared"}\n')
    atomic(target, (stage / "payload" / HOME).read_bytes(), 0o644)
    require(sha(target) == row["sha256"], "media-top-rail-install-drift")
    atomic(checkpoint / "state.json", b'{"state":"installed"}\n')
    return {"installed": True, "checkpoint_verified": True}
