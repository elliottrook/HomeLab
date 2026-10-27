"""Exact two-file repair for the Acquisition Hub primary action label."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


PARENT = Path(".aster-checkpoints/aster-acquisition-label8/manifest.json")
PARENT_STATE = Path(".aster-checkpoints/aster-acquisition-label8/state.json")
CHECKPOINT = Path(".aster-checkpoints/aster-acquisition-label9")


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)),
            "acquisition-label-linked-path")


def atomic(path, raw, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".acquisition-label.",
                                              dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def inspect(stage, pin):
    stage = Path(stage)
    require(re.fullmatch("[0-9a-f]{64}", pin or "") is not None,
            "acquisition-label-pin-format")
    safe(stage / "manifest.json")
    require(sha(stage / "manifest.json") == pin,
            "acquisition-label-manifest-pin")
    manifest = json.loads((stage / "manifest.json").read_text())
    require(manifest.get("schema") == 1
            and manifest.get("kind") == "hp-acquisition-label-patch.v2"
            and set(manifest) == {"schema", "kind", "parent_manifest_sha256",
                                  "files", "helper_sha256"}
            and re.fullmatch("[0-9a-f]{64}",
                             manifest.get("parent_manifest_sha256", ""))
            and isinstance(manifest.get("files"), list),
            "acquisition-label-contract")
    expected = {
        ".kodi/addons/script.asteracquisition/default.py",
        ".kodi/addons/skin.asterhome/1080i/custom_1133_acquisition.xml",
    }
    require({row.get("path") for row in manifest["files"]} == expected,
            "acquisition-label-shape")
    helper = stage / "acquisition_label_patch_install.py"
    safe(helper)
    require(helper.is_file() and sha(helper) == manifest["helper_sha256"],
            "acquisition-label-helper-drift")
    for row in manifest["files"]:
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts
                and re.fullmatch("[0-9a-f]{64}", row.get("before_sha256", ""))
                and re.fullmatch("[0-9a-f]{64}", row.get("sha256", "")),
                "acquisition-label-path")
        payload = stage / "payload" / relative
        safe(payload)
        require(payload.is_file() and payload.stat().st_size == row.get("bytes")
                and sha(payload) == row["sha256"],
                "acquisition-label-payload-drift")
    return manifest


def verify_files(manifest, storage, field):
    for row in manifest["files"]:
        target = Path(storage) / row["path"]
        safe(target)
        require(target.is_file() and sha(target) == row[field],
                "acquisition-label-active-drift")


def run(mode, stage, storage, pin, *, stopped):
    require(mode in ("install", "verify", "rollback"),
            "acquisition-label-mode")
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, pin)
    require((storage / PARENT).is_file()
            and sha(storage / PARENT) == manifest["parent_manifest_sha256"]
            and json.loads((storage / PARENT_STATE).read_text()).get("state")
            == "installed", "acquisition-label-parent-drift")
    checkpoint = storage / CHECKPOINT
    if mode == "verify":
        require(checkpoint.is_dir(), "acquisition-label-checkpoint-missing")
        state = json.loads((checkpoint / "state.json").read_text()).get("state")
        require(state in ("installed", "rolled_back"),
                "acquisition-label-state")
        verify_files(manifest, storage,
                     "sha256" if state == "installed" else "before_sha256")
        return {"verified": True, "active": state == "installed"}
    require(stopped(), "acquisition-label-stop-kodi-first")
    if mode == "rollback":
        require(checkpoint.is_dir()
                and json.loads((checkpoint / "state.json").read_text()).get("state")
                == "installed", "acquisition-label-not-active")
        verify_files(manifest, storage, "sha256")
        for row in manifest["files"]:
            atomic(storage / row["path"],
                   (checkpoint / "original" / row["path"]).read_bytes(), 0o644)
        atomic(checkpoint / "state.json", b'{"state":"rolled_back"}\n')
        verify_files(manifest, storage, "before_sha256")
        return {"rolled_back": True, "recovery_retained": True}
    require(not checkpoint.exists(), "acquisition-label-checkpoint-exists")
    verify_files(manifest, storage, "before_sha256")
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint / "manifest.json", (stage / "manifest.json").read_bytes())
    for row in manifest["files"]:
        target = storage / row["path"]
        atomic(checkpoint / "original" / row["path"], target.read_bytes())
        atomic(target, (stage / "payload" / row["path"]).read_bytes(), 0o644)
    atomic(checkpoint / "state.json", b'{"state":"installed"}\n')
    verify_files(manifest, storage, "sha256")
    return {"installed": True, "checkpoint_verified": True,
            "files": len(manifest["files"])}
