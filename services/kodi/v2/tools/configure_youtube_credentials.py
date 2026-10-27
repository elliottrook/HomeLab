"""Interactive HP-only credential handoff for official plugin.video.youtube.

Run this directly over an interactive SSH session.  Values are collected with
hidden prompts, never accepted on the command line, and never printed.  The
pre-credential add-on state is checkpointed locally with restrictive modes.
"""

from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE = Path("/storage/.kodi/userdata/addon_data/plugin.video.youtube")
API_KEYS = BASE / "api_keys.json"
SETTINGS = BASE / "settings.xml"
ACCESS = BASE / "access_manager.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-youtube-api-20261026")
MODULE_DIR = Path("/storage/.aster-staging/aster-youtube-integration3")

sys.path.insert(0, str(MODULE_DIR))
from youtube_credentials import configure, configured, normalize  # noqa: E402


def require(value: bool, code: str) -> None:
    if not value:
        raise RuntimeError(code)


def kodi_active() -> bool:
    result = subprocess.run(["systemctl", "is-active", "--quiet", "kodi"], check=False)
    return result.returncode == 0


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".aster-youtube-", dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def checkpoint() -> bool:
    if CHECKPOINT.exists():
        state_path = CHECKPOINT / "state.json"
        require(state_path.exists(), "checkpoint-incomplete")
        state = json.loads(state_path.read_text())
        require(state.get("schema") == "aster.youtube.credentials.checkpoint.v1",
                "checkpoint-schema")
        require(not (CHECKPOINT / "rolled-back.json").exists(),
                "checkpoint-already-rolled-back")
        tracked = {API_KEYS.name, SETTINGS.name, ACCESS.name}
        require(set(state.get("present", [])) | set(state.get("absent", [])) == tracked,
                "checkpoint-incomplete")
        for name in state.get("present", []):
            require((CHECKPOINT / (name + ".before")).exists(), "checkpoint-incomplete")
        return True
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    present = []
    absent = []
    for path in (API_KEYS, SETTINGS, ACCESS):
        if path.exists():
            shutil.copyfile(path, CHECKPOINT / (path.name + ".before"))
            os.chmod(CHECKPOINT / (path.name + ".before"), 0o600)
            present.append(path.name)
        else:
            absent.append(path.name)
    atomic_write(CHECKPOINT / "state.json", json.dumps({
        "schema": "aster.youtube.credentials.checkpoint.v1",
        "present": sorted(present),
        "absent": sorted(absent),
        "contains_preexisting_client_state": True,
    }, indent=2).encode("utf-8") + b"\n")
    return False


def install() -> dict[str, object]:
    require(os.uname().nodename == "AsterTV", "hp-only-no-production")
    require(not kodi_active(), "stop-kodi-before-credential-write")
    checkpoint_reused = checkpoint()
    existing = API_KEYS.read_bytes() if API_KEYS.exists() else b"{}\n"
    credentials = normalize(
        getpass.getpass("YouTube Data API key (hidden): "),
        getpass.getpass("OAuth client ID (hidden): "),
        getpass.getpass("OAuth client secret (hidden): "),
    )
    candidate = configure(existing, credentials)
    atomic_write(API_KEYS, candidate)
    require(configured(API_KEYS.read_bytes()), "credential-verification-failed")
    return {"ok": True, "configured": True, "checkpoint": str(CHECKPOINT),
            "checkpoint_reused": checkpoint_reused, "values_printed": False,
            "restart_kodi": True}


def verify() -> dict[str, object]:
    require(os.uname().nodename == "AsterTV", "hp-only-no-production")
    require(API_KEYS.exists() and configured(API_KEYS.read_bytes()), "credentials-not-configured")
    require((API_KEYS.stat().st_mode & 0o077) == 0, "credential-file-mode-too-broad")
    return {"ok": True, "configured": True, "file_mode": "owner-only",
            "values_printed": False}


def migrate() -> dict[str, object]:
    """Move a documented ``personal`` set into v7.4.4's runtime ``user`` slot."""
    require(os.uname().nodename == "AsterTV", "hp-only-no-production")
    require(not kodi_active(), "stop-kodi-before-credential-write")
    existing = API_KEYS.read_bytes() if API_KEYS.exists() else b"{}\n"
    if configured(existing):
        return {"ok": True, "configured": True, "migrated": False,
                "values_printed": False, "restart_kodi": True}
    document = json.loads(existing.decode("utf-8"))
    personal = document.get("keys", {}).get("personal", {})
    require(isinstance(personal, dict), "personal-credential-slot-missing")
    credentials = normalize(
        personal.get("api_key", ""),
        personal.get("client_id", ""),
        personal.get("client_secret", ""),
    )
    atomic_write(API_KEYS, configure(existing, credentials))
    require(configured(API_KEYS.read_bytes()), "credential-migration-verification-failed")
    return {"ok": True, "configured": True, "migrated": True,
            "values_printed": False, "restart_kodi": True}


def rollback() -> dict[str, object]:
    require(os.uname().nodename == "AsterTV", "hp-only-no-production")
    require(not kodi_active(), "stop-kodi-before-credential-rollback")
    state = json.loads((CHECKPOINT / "state.json").read_text())
    for path in (API_KEYS, SETTINGS, ACCESS):
        before = CHECKPOINT / (path.name + ".before")
        if path.name in state["present"]:
            atomic_write(path, before.read_bytes())
        elif path.exists():
            path.unlink()
    atomic_write(CHECKPOINT / "rolled-back.json", b'{"ok": true, "secrets_removed": true}\n')
    return {"ok": True, "rolled_back": True, "values_printed": False}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) == 2 else "verify"
    require(mode in {"install", "migrate", "verify", "rollback"}, "mode")
    result = {"install": install, "migrate": migrate,
              "verify": verify, "rollback": rollback}[mode]()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"ok": False, "code": str(error), "values_printed": False}))
        raise SystemExit(1)

