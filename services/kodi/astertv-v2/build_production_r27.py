#!/usr/bin/env python3
"""Build the immutable r27 recovery bundle from the accepted r21 snapshot."""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[3]
DIST = ROOT / "services/kodi/dist"
SOURCE = DIST / "astertv-v2.0.7-production-2026-10-30-r21.tar.gz"
OUTPUT = DIST / "astertv-v2.0.7-production-2026-10-30-r27.tar.gz"
PREFIX = "aster-v2-package/"
OLD_RELEASE = "astertv-v2.0.7-production-2026-10-30-r21"
RELEASE = "astertv-v2.0.7-production-2026-10-30-r27"
CAMERA_ENTRY = "<onload>RunScript(script.asterruntime,aster-camera2,view,entry)</onload>"
CAMERA_LEAVE = "<onunload>RunScript(script.asterruntime,aster-camera2,view,leave)</onunload>"
HOME_ENTRY = "<onload>RunScript(script.asterruntime,aster-home-status1,default,entry)</onload>"
HOME_LEAVE = "<onunload>RunScript(script.asterruntime,aster-home-status1,default,leave)</onunload>"
EXTRA = (
    "apply_production_ebook_boundary_r22_fix.py",
    "apply_production_ebook_data_link_r23_fix.py",
    "apply_production_home_firewall_r24.py",
    "apply_production_home_receiver_r24.py",
    "apply_production_home_receiver_destination_r25.py",
    "apply_home_delivery_dual_target_r24.py",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main() -> None:
    with tarfile.open(SOURCE, "r:gz") as archive:
        members = {member.name: (copy.copy(member), archive.extractfile(member).read()
                   if member.isfile() else None) for member in archive.getmembers()}

    snapshot_root = PREFIX + "lab-addon-snapshot/"
    home_name = snapshot_root + "skin.asterhome/1080i/custom_1112_home.xml"
    family_name = snapshot_root + "script.asterruntime/family-manifest.json"
    home = members[home_name][1].decode()
    if home.count(CAMERA_ENTRY) != 1 or home.count(CAMERA_LEAVE) != 1:
        raise RuntimeError("r21 camera lifecycle mismatch")
    if HOME_ENTRY in home or HOME_LEAVE in home:
        raise RuntimeError("r21 already contains Home lifecycle hook")
    home = home.replace(CAMERA_ENTRY, CAMERA_ENTRY + HOME_ENTRY, 1)
    home = home.replace(CAMERA_LEAVE, HOME_LEAVE + CAMERA_LEAVE, 1)
    home_data = home.encode()
    members[home_name] = (members[home_name][0], home_data)

    family = json.loads(members[family_name][1])
    family["skin"]["1080i/custom_1112_home.xml"] = sha(home_data)
    family_data = encoded(family)
    members[family_name] = (members[family_name][0], family_data)

    snapshot_name = PREFIX + "lab-addon-snapshot-manifest.json"
    snapshot = json.loads(members[snapshot_name][1])
    if snapshot.get("release") != OLD_RELEASE or len(snapshot.get("files", [])) != 577:
        raise RuntimeError("unexpected r21 snapshot")
    snapshot["release"] = RELEASE
    replacements = {
        "skin.asterhome/1080i/custom_1112_home.xml": home_data,
        "script.asterruntime/family-manifest.json": family_data,
    }
    for row in snapshot["files"]:
        data = replacements.get(row["path"])
        if data is not None:
            row["bytes"] = len(data)
            row["sha256"] = sha(data)
    snapshot_data = encoded(snapshot)
    members[snapshot_name] = (members[snapshot_name][0], snapshot_data)

    promoter_name = PREFIX + "reconciliation/promote_v207_to_production.py"
    promoter = members[promoter_name][1].decode()
    promoter = promoter.replace("production-r21-20261030", "production-r27-20261030")
    promoter = promoter.replace(OLD_RELEASE, RELEASE)
    if OLD_RELEASE in promoter or "production-r21-20261030" in promoter:
        raise RuntimeError("promoter release replacement incomplete")
    promoter_data = promoter.encode()
    members[promoter_name] = (members[promoter_name][0], promoter_data)

    reconciliation = ROOT / "services/kodi/astertv-v2/reconciliation"
    extras: dict[str, bytes] = {}
    for filename in EXTRA:
        data = (reconciliation / filename).read_bytes()
        compile(data, filename, "exec")
        extras["reconciliation/" + filename] = data
    home_entry = (reconciliation / "apply_production_home_entry_r27_fix.py").read_bytes()
    compile(home_entry, "apply_production_home_entry_r27_fix.py", "exec")
    extras["reconciliation/apply_production_home_entry_r27_fix.py"] = home_entry
    for filename in ("delivery.py", "known_hosts"):
        extras["reconciliation/payload/home-delivery/" + filename] = (
            reconciliation / "payload/home-delivery" / filename).read_bytes()

    template = copy.copy(members[promoter_name][0])
    for relative, data in extras.items():
        name = PREFIX + relative
        info = copy.copy(template)
        info.name = name
        info.mode = 0o755 if relative.endswith(".py") else 0o644
        info.size = len(data)
        members[name] = (info, data)

    readme_name = PREFIX + "README.txt"
    readme = members[readme_name][1].decode()
    heading = f"""# AsterTV v2.0.7 production recovery release r27 — 2026-10-30

r27 supersedes r21. It preserves the accepted 577-file v2 UI and adds the
production Home lifecycle fix so all 63 Home Assistant readings repopulate on
every Smart Home page entry while the camera entry/leave hooks remain intact.
It also carries the checkpointed eBook boundary/data-link and dual-target Home
feed recovery installers. These external-state installers remain guarded and
must be applied only in their documented order; no credentials, Kodi profile,
Home Assistant private key, narration output or audio configuration is bundled.

"""
    readme_data = (heading + readme.replace(
        "# AsterTV v2.0.7 production recovery release r21 — 2026-10-30\n\n", "", 1)).encode()
    members[readme_name] = (members[readme_name][0], readme_data)

    manifest_name = PREFIX + "manifest.json"
    manifest = json.loads(members[manifest_name][1])
    manifest["release"] = RELEASE
    manifest["source_commit"] = "095cccfa"
    manifest["artifacts"]["lab-addon-snapshot-manifest.json"] = sha(snapshot_data)
    manifest["artifacts"]["reconciliation/promote_v207_to_production.py"] = sha(promoter_data)
    for relative, data in sorted(extras.items()):
        manifest["artifacts"][relative] = sha(data)
    manifest["promotion_guards"].extend((
        "home-data-entry-and-leave-hooks-preserve-camera-lifecycle",
        "external-ebook-and-home-feed-repairs-carried-as-checkpointed-guarded-installers",
    ))
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
    sidecar = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
    sidecar.write_text(f"{sha(OUTPUT.read_bytes())}  {OUTPUT.name}\n")
    print(f"{OUTPUT} {sha(OUTPUT.read_bytes())}")


if __name__ == "__main__":
    main()
