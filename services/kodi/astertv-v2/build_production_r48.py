#!/usr/bin/env python3
"""Build r48 from r47 with the accepted full-colour Genre art treatment."""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "services/kodi/astertv-v2"
DIST = ROOT / "services/kodi/dist"
SOURCE = DIST / "astertv-v2.0.7-production-2026-10-31-r47.tar.gz"
OUTPUT = DIST / "astertv-v2.0.7-production-2026-10-31-r48.tar.gz"
PREFIX = "aster-v2-package/"
OLD_RELEASE = "astertv-v2.0.7-production-2026-10-31-r47"
RELEASE = "astertv-v2.0.7-production-2026-10-31-r48"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main() -> None:
    with tarfile.open(SOURCE, "r:gz") as archive:
        members = {
            member.name: (
                copy.copy(member),
                archive.extractfile(member).read() if member.isfile() else None,
            )
            for member in archive.getmembers()
        }

    snapshot_root = PREFIX + "lab-addon-snapshot/"
    include_relative = "skin.asterhome/1080i/Includes.xml"
    family_relative = "script.asterruntime/family-manifest.json"
    includes = (HERE / "reconciliation/payload" / include_relative).read_bytes()
    test_path = HERE / "reconciliation/test_production_genre_art_r48.py"
    test = test_path.read_bytes()
    compile(test, test_path.name, "exec")

    family_name = snapshot_root + family_relative
    family = json.loads(members[family_name][1])
    family["skin"]["1080i/Includes.xml"] = sha(includes)
    family_data = encoded(family)
    replacements = {include_relative: includes, family_relative: family_data}
    for relative, data in replacements.items():
        members[snapshot_root + relative] = (members[snapshot_root + relative][0], data)

    snapshot_name = PREFIX + "lab-addon-snapshot-manifest.json"
    snapshot = json.loads(members[snapshot_name][1])
    if snapshot["release"] != OLD_RELEASE or len(snapshot["files"]) != 577:
        raise RuntimeError("unexpected r47 snapshot")
    snapshot["release"] = RELEASE
    pending = set(replacements)
    for row in snapshot["files"]:
        if row["path"] in replacements:
            data = replacements[row["path"]]
            row["bytes"] = len(data)
            row["sha256"] = sha(data)
            pending.remove(row["path"])
    if pending:
        raise RuntimeError("snapshot replacements missing: " + repr(pending))
    snapshot_data = encoded(snapshot)
    members[snapshot_name] = (members[snapshot_name][0], snapshot_data)

    promoter_name = PREFIX + "reconciliation/promote_v207_to_production.py"
    promoter = members[promoter_name][1].decode()
    promoter = promoter.replace(OLD_RELEASE, RELEASE)
    promoter = promoter.replace("production-r47-20261031", "production-r48-20261031")
    if OLD_RELEASE in promoter or "production-r47-20261031" in promoter:
        raise RuntimeError("promoter release replacement incomplete")
    compile(promoter, "promote_v207_to_production.py", "exec")
    promoter_data = promoter.encode()
    members[promoter_name] = (members[promoter_name][0], promoter_data)

    test_relative = "reconciliation/test_production_genre_art_r48.py"
    test_name = PREFIX + test_relative
    info = copy.copy(members[promoter_name][0])
    info.name, info.mode, info.size = test_name, 0o755, len(test)
    members[test_name] = (info, test)

    readme_name = PREFIX + "README.txt"
    heading = f"""# AsterTV v2.0.7 production release r48 — 2026-10-31

r48 supersedes r47 without changing its accepted Resume, playback, Search,
HDR, Dolby or navigation behaviour. Media Genre posters now retain full colour,
use a persistent sage edge and charcoal title ribbon, and change to gold on
focus. The previous ivory wash is removed.

"""
    members[readme_name] = (
        members[readme_name][0],
        (heading + members[readme_name][1].decode()).encode(),
    )

    manifest_name = PREFIX + "manifest.json"
    manifest = json.loads(members[manifest_name][1])
    manifest["release"] = RELEASE
    manifest["source_commit"] = "352726c8+r48"
    manifest["artifacts"]["lab-addon-snapshot-manifest.json"] = sha(snapshot_data)
    manifest["artifacts"]["reconciliation/promote_v207_to_production.py"] = sha(promoter_data)
    manifest["artifacts"][test_relative] = sha(test)
    manifest["promotion_guards"].append("full-colour-genre-art-and-routes-pinned")
    members[manifest_name] = (members[manifest_name][0], encoded(manifest))

    with OUTPUT.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for name in sorted(members):
                    info, data = members[name]
                    info.name = name
                    info.uid = info.gid = 0
                    info.uname = info.gname = "root"
                    info.mtime = 0
                    if data is None:
                        archive.addfile(info)
                    else:
                        info.size = len(data)
                        archive.addfile(info, io.BytesIO(data))
    digest = sha(OUTPUT.read_bytes())
    OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
        f"{digest}  {OUTPUT.name}\n"
    )
    print(f"{OUTPUT} {digest}")


if __name__ == "__main__":
    main()
