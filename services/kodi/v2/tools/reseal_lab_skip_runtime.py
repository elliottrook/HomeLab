"""Reseal lab Search/movie guard after the Aster recap helper changes hash."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import time


ROOT = Path("/storage/.kodi/addons")
RUNTIME = ROOT / "script.asterruntime"
COMPONENT = RUNTIME / "aster-global-search-ui22"
MOVIE = COMPONENT / "resources/lib/movie_player.py"
MANIFEST = COMPONENT / "manifest.json"
FAMILY = RUNTIME / "family-manifest.json"
SKIP = ROOT / "skin.asterhome/tools/next_episode.py"
NAV = ROOT / "skin.asterhome/1080i/MyVideoNav.xml"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-skip-runtime-20261029")
OLD = b"8fe18880de923443734fde26dd0c47815e93c68c531e9a34103630054e22c102"
NEW = b"909a321aee7e6e68121e7149c26086c56faa314c303d4843510d11e05ed7e3ba"
OLD_PLAYER = b"21b93325b6ef9b50fdd3f5c48b273e12820f5a662ae534405dacdebcc15388fd"
NEW_PLAYER = b"a4532bcc3b7a3508b67b9a00cadb6523e763d9510db12dc8f1f53c74c5459112"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, data):
    fd, name = tempfile.mkstemp(prefix=".aster-reseal-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, path.stat().st_mode & 0o777)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def main():
    if os.uname().nodename != "AsterTV" or (CHECKPOINT / "installed.json").exists():
        raise RuntimeError("lab-preflight")
    proof = Path("/storage/.aster-checkpoints/astertv-lab-skip-probe-20261029.json")
    if time.time() - proof.stat().st_mtime > 20 or json.loads(proof.read_text()).get("playing_any") is not False:
        raise RuntimeError("fresh-idle-proof-required")
    paths = (MOVIE, MANIFEST, FAMILY, SKIP, NAV)
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise RuntimeError("file-boundary")
    if digest(SKIP.read_bytes()) != NEW.decode():
        raise RuntimeError("skip-helper-drift")
    player = ROOT / "plugin.video.jellyfin/jellyfin_kodi/player.py"
    if not player.is_file() or player.is_symlink() or digest(player.read_bytes()) != NEW_PLAYER.decode():
        raise RuntimeError("jellyfin-player-drift")
    movie = MOVIE.read_bytes()
    recovering = CHECKPOINT.exists()
    if (movie.count(OLD_PLAYER) != 1 or NEW_PLAYER in movie
            or movie.count(NEW if recovering else OLD) != 1):
        raise RuntimeError("movie-guard-predecessor")
    if recovering and (not all((CHECKPOINT / name).is_file() for name in
                           ("movie_player.py.before", "manifest.json.before", "family-manifest.json.before"))):
        raise RuntimeError("incomplete-recovery-checkpoint")
    component = json.loads(MANIFEST.read_text())
    family = json.loads(FAMILY.read_text())
    rows = [row for row in component["files"] if row["path"] == "resources/lib/movie_player.py"]
    if (len(rows) != 1 or rows[0]["sha256"] != digest(movie)
            or rows[0]["bytes"] != len(movie)
            or family["components"]["aster-global-search-ui22"]["manifest_sha256"] != digest(MANIFEST.read_bytes())):
        raise RuntimeError("manifest-predecessor-drift")
    if not recovering:
        CHECKPOINT.mkdir(mode=0o700, parents=True)
        for source, name in ((MOVIE, "movie_player.py.before"), (MANIFEST, "manifest.json.before"),
                             (FAMILY, "family-manifest.json.before")):
            shutil.copy2(source, CHECKPOINT / name)
            os.chmod(CHECKPOINT / name, 0o600)
    new_movie = movie.replace(OLD, NEW, 1).replace(OLD_PLAYER, NEW_PLAYER, 1)
    rows[0]["sha256"] = digest(new_movie)
    rows[0]["bytes"] = len(new_movie)
    new_manifest = (json.dumps(component, indent=2, sort_keys=True) + "\n").encode()
    family["components"]["aster-global-search-ui22"]["manifest_sha256"] = digest(new_manifest)
    family["skin"]["1080i/MyVideoNav.xml"] = digest(NAV.read_bytes())
    new_family = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()
    atomic(MOVIE, new_movie)
    atomic(MANIFEST, new_manifest)
    atomic(FAMILY, new_family)
    spec = importlib.util.spec_from_file_location("aster_movie_guard", MOVIE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.verify_stage()
    (CHECKPOINT / "installed.json").write_text('{"ok": true, "skip_helper": "recap-capable"}\n')
    print("lab Search/movie guard resealed and verified")


if __name__ == "__main__":
    main()
