"""Exact, reversible install of Aster's discovery-only Acquisition Hub."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


ADDON = Path(".kodi/addons/script.asteracquisition")
SKIN = Path(".kodi/addons/skin.asterhome")
CHECKPOINT = Path(".aster-checkpoints/aster-acquisition-page1")
ADDON_MEMBERS = {
    "addon.xml", "default.py",
    "resources/lib/acquisition_hub_model.py",
    "resources/lib/acquisition_page_model.py",
    "resources/lib/discovery_feed_client.py",
    "resources/lib/landing_recommendations.py",
}
SKIN_MEMBERS = {"1080i/Home.xml", "1080i/custom_1133_acquisition.xml"}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)),
            "acquisition-install-linked-path")


def atomic(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".acquisition-install.",
                                              dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _row(stage, root, row, seen, code):
    relative = Path(row.get("path", ""))
    require(relative.parts and not relative.is_absolute()
            and ".." not in relative.parts
            and relative.as_posix() not in seen, code + "-path")
    seen.add(relative.as_posix())
    payload = Path(stage) / root / relative
    safe(payload)
    require(payload.is_file() and payload.stat().st_size == row.get("bytes")
            and sha(payload) == row.get("sha256"), code + "-drift")
    return relative


def inspect(stage, pin):
    stage = Path(stage)
    require(re.fullmatch("[0-9a-f]{64}", pin or "") is not None,
            "acquisition-install-pin-format")
    safe(stage / "manifest.json")
    require(sha(stage / "manifest.json") == pin,
            "acquisition-install-manifest-pin")
    manifest = json.loads((stage / "manifest.json").read_text())
    require(manifest.get("schema") == 1
            and manifest.get("kind") == "hp-acquisition-page.v1"
            and manifest.get("addon") == "script.asteracquisition"
            and manifest.get("writes_enabled") is False,
            "acquisition-install-contract")
    require(manifest.get("activation") == "RunScript(script.asteracquisition)"
            and set(manifest.get("helpers", {})) == {"acquisition_install.py"}
            and isinstance(manifest.get("addon_files"), list)
            and isinstance(manifest.get("skin"), list),
            "acquisition-install-shape")
    require(sha(stage / "acquisition_install.py")
            == manifest["helpers"]["acquisition_install.py"],
            "acquisition-install-helper-drift")
    seen = set()
    for row in manifest["addon_files"]:
        _row(stage, "script.asteracquisition", row, seen,
             "acquisition-install-addon")
    require(seen == ADDON_MEMBERS, "acquisition-install-addon-shape")
    seen = set()
    for row in manifest["skin"]:
        _row(stage, "skin", row, seen, "acquisition-install-skin")
        before = row.get("before_sha256")
        require(before is None or re.fullmatch("[0-9a-f]{64}", before),
                "acquisition-install-skin-drift")
    require(seen == SKIN_MEMBERS, "acquisition-install-skin-shape")
    return manifest


def verify_addon(folder, rows):
    folder = Path(folder)
    require(folder.is_dir() and not folder.is_symlink(),
            "acquisition-install-addon-missing")
    expected = {row["path"]: row for row in rows}
    for relative, row in expected.items():
        path = folder / relative
        safe(path)
        require(path.is_file() and path.stat().st_size == row["bytes"]
                and sha(path) == row["sha256"],
                "acquisition-install-active-addon-drift")
    for path in folder.rglob("*"):
        if path.is_dir() and not path.is_symlink():
            continue
        relative = path.relative_to(folder).as_posix()
        require(relative in expected or (not path.is_symlink()
                and "__pycache__" in path.parts and path.suffix == ".pyc"),
                "acquisition-install-unexpected-addon-file")


def _checkpoint(stage, storage, pin):
    manifest = inspect(stage, pin)
    checkpoint = Path(storage) / CHECKPOINT
    require(checkpoint.is_dir() and sha(checkpoint / "manifest.json") == pin,
            "acquisition-install-checkpoint")
    state = json.loads((checkpoint / "state.json").read_text()).get("state")
    require(state in ("prepared", "installed", "rolled_back"),
            "acquisition-install-state")
    for row in manifest["skin"]:
        if row["before_sha256"] is None:
            require((checkpoint / "absent" / row["path"]).is_file(),
                    "acquisition-install-absence-record")
        else:
            backup = checkpoint / "original" / row["path"]
            require(backup.is_file() and sha(backup) == row["before_sha256"],
                    "acquisition-install-recovery-drift")
    return manifest, state


def verify_active(stage, storage, pin):
    manifest, state = _checkpoint(stage, storage, pin)
    active = state == "installed"
    addon = Path(storage) / ADDON
    if active:
        verify_addon(addon, manifest["addon_files"])
    else:
        require(not addon.exists(), "acquisition-install-addon-after-rollback")
    for row in manifest["skin"]:
        target = Path(storage) / SKIN / row["path"]
        if active:
            require(target.is_file() and sha(target) == row["sha256"],
                    "acquisition-install-active-skin-drift")
        elif row["before_sha256"] is None:
            require(not target.exists(),
                    "acquisition-install-absent-not-restored")
        else:
            require(target.is_file() and sha(target) == row["before_sha256"],
                    "acquisition-install-skin-not-restored")
    return active


def _restore(manifest, storage, checkpoint):
    storage = Path(storage)
    addon = storage / ADDON
    if addon.exists():
        verify_addon(addon, manifest["addon_files"])
        os.rename(addon, checkpoint / "retired-addon")
    for row in manifest["skin"]:
        target = storage / SKIN / row["path"]
        require(not target.exists()
                or sha(target) in (row["sha256"], row["before_sha256"]),
                "acquisition-install-rollback-drift")
        if row["before_sha256"] is None:
            if target.exists():
                os.unlink(target)
        else:
            atomic(target, (checkpoint / "original" / row["path"]).read_bytes())


def run(mode, stage, storage, pin, *, idle):
    require(mode in ("install", "verify", "rollback"),
            "acquisition-install-mode")
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, pin)
    require(idle(), "acquisition-install-home-idle-required")
    checkpoint, addon = storage / CHECKPOINT, storage / ADDON
    if mode == "verify":
        return {"verified": True,
                "active": verify_active(stage, storage, pin)}
    if mode == "rollback":
        _, state = _checkpoint(stage, storage, pin)
        require(state == "installed", "acquisition-install-not-active")
        _restore(manifest, storage, checkpoint)
        atomic(checkpoint / "state.json", b'{"state":"rolled_back"}\n')
        verify_active(stage, storage, pin)
        return {"rolled_back": True, "recovery_retained": True}
    require(not addon.exists(), "acquisition-install-addon-already-exists")
    for row in manifest["skin"]:
        target = storage / SKIN / row["path"]
        require((row["before_sha256"] is None and not target.exists())
                or (row["before_sha256"] is not None and target.is_file()
                    and sha(target) == row["before_sha256"]),
                "acquisition-install-exact-predecessor")
    require(not checkpoint.exists(), "acquisition-install-checkpoint-exists")
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint / "manifest.json", (stage / "manifest.json").read_bytes())
    for row in manifest["skin"]:
        if row["before_sha256"] is None:
            atomic(checkpoint / "absent" / row["path"], b"absent\n")
        else:
            atomic(checkpoint / "original" / row["path"],
                   (storage / SKIN / row["path"]).read_bytes())
    atomic(checkpoint / "state.json", b'{"state":"prepared"}\n')
    require(idle(), "acquisition-install-home-idle-required")
    temporary = addon.with_name(addon.name + ".installing")
    try:
        temporary.mkdir(parents=True, mode=0o700)
        for row in manifest["addon_files"]:
            atomic(temporary / row["path"],
                   (stage / "script.asteracquisition" / row["path"]).read_bytes())
        verify_addon(temporary, manifest["addon_files"])
        os.rename(temporary, addon)
        for row in manifest["skin"]:
            atomic(storage / SKIN / row["path"],
                   (stage / "skin" / row["path"]).read_bytes())
        atomic(checkpoint / "state.json", b'{"state":"installed"}\n')
        verify_active(stage, storage, pin)
    except Exception:
        if temporary.exists():
            os.rename(temporary, checkpoint / "failed-addon")
        if addon.exists():
            _restore(manifest, storage, checkpoint)
        atomic(checkpoint / "state.json", b'{"state":"rolled_back"}\n')
        raise
    return {"installed": True, "checkpoint_verified": True,
            "addon_files": len(manifest["addon_files"]),
            "skin_files": len(manifest["skin"])}
