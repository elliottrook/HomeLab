#!/usr/bin/env python3
"""Re-pin r10 runtime members after the Kodi 22 acceptance repairs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile


ROOT = Path("/storage/.kodi/addons")
RUNTIME = ROOT / "script.asterruntime"
SKIN = ROOT / "skin.asterhome"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-acceptance-r10-manifests-20261030")
EXPECTED_FAMILY = "617a134b0fe9721b1bd25c6b0051207cce46b439b41d2e3657937e432e7bc30b"
EXPECTED_WRAPPER = "852379c6583a6da89c229a7e89e96dae739971c720dc29d546ef16a2dd5dfe47"
EXPECTED_DIGEST_XML = "6da50f75fe9a9d953ae25880a7b91e0b3a621af810f6073b1adb0651430c650f"
OLD_PLAYER_PIN = "a25aad49d2d3ec2399775a809b96cfc0b2479ca14bd19dbc285d1966bcc1c8aa"
# This stale reader pin predated r9 and is the independent cause of the
# checklist's reader failure.
OLD_READER_PIN = "a8474501c9141bb220726c118b58e0941d9de2c3c42e2280410dbf3b1e5b3c86"
CHANGED_COMPONENTS = {
    "aster-camera2": {"view.py": "5cf2ffc7b74df3dcdd4651c4f1984b1aed233404146551945c4cd7e40982d1df"},
    "aster-digest-player8": {"default.py": "c087594e45ef1312ac076c965b90de72d88ba3fe8f5e238a1f914f9ce9e575c5"},
    "aster-digest-reader6": {"default.py": "abef059485c8caf32d193574469cdd9d96cb62cc52d9574a0eae2d71f25b38fa"},
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def active_players():
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def component_candidate(name: str) -> bytes:
    directory = RUNTIME / name
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("component") != name:
        raise RuntimeError("component identity mismatch: " + name)
    expected_changes = CHANGED_COMPONENTS[name]
    seen = set()
    for row in manifest["files"]:
        path = directory / row["path"]
        data = path.read_bytes()
        digest = sha(data)
        if row["path"] in expected_changes:
            if digest != expected_changes[row["path"]]:
                raise RuntimeError("changed member mismatch: " + name + "/" + row["path"])
            seen.add(row["path"])
        elif digest != row["sha256"] or len(data) != row["bytes"]:
            raise RuntimeError("unrelated component drift: " + name + "/" + row["path"])
        row["sha256"] = digest
        row["bytes"] = len(data)
    if seen != set(expected_changes):
        raise RuntimeError("changed component member missing: " + name)
    return encoded(manifest)


def replace_pin(path: Path, expected_hash: str, old: str, new: str) -> bytes:
    data = path.read_bytes()
    if sha(data) != expected_hash:
        raise RuntimeError("unexpected pin consumer hash: " + str(path))
    text = data.decode()
    if text.count(old) != 1:
        raise RuntimeError("pin replacement count: " + str(path))
    return text.replace(old, new, 1).encode()


def family_candidate(component_manifests: dict[str, bytes], wrapper: bytes,
                     digest_xml: bytes) -> bytes:
    path = RUNTIME / "family-manifest.json"
    data = path.read_bytes()
    if sha(data) != EXPECTED_FAMILY:
        raise RuntimeError("unexpected family manifest hash")
    family = json.loads(data)
    for name, candidate in component_manifests.items():
        family["components"][name]["manifest_sha256"] = sha(candidate)
    # Reconcile every recorded skin guard to the installed r10 member.  This
    # also absorbs the already-reviewed r9 rail, Books and selection repairs
    # that the old family manifest had not learned about.
    for relative in family["skin"]:
        if relative == "tools/aster_v2_digest.py":
            member = wrapper
        elif relative == "1080i/custom_1111_digest.xml":
            member = digest_xml
        else:
            member = (SKIN / relative).read_bytes()
        family["skin"][relative] = sha(member)
    return encoded(family)


def atomic_write(path: Path, data: bytes):
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r10-pin-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    active_players()
    components = {name: component_candidate(name) for name in CHANGED_COMPONENTS}
    player_pin = sha(components["aster-digest-player8"])
    reader_pin = sha(components["aster-digest-reader6"])
    wrapper_path = SKIN / "tools/aster_v2_digest.py"
    digest_xml_path = SKIN / "1080i/custom_1111_digest.xml"
    wrapper = replace_pin(wrapper_path, EXPECTED_WRAPPER, OLD_PLAYER_PIN, player_pin)
    digest_xml = replace_pin(digest_xml_path, EXPECTED_DIGEST_XML, OLD_READER_PIN, reader_pin)
    family = family_candidate(components, wrapper, digest_xml)
    candidates = {
        **{RUNTIME / name / "manifest.json": data for name, data in components.items()},
        wrapper_path: wrapper,
        digest_xml_path: digest_xml,
        RUNTIME / "family-manifest.json": family,
    }
    CHECKPOINT.mkdir(mode=0o700)
    evidence = {"kind": "astertv-v2-r10-runtime-repin", "files": {}}
    for path, candidate in candidates.items():
        relative = str(path.relative_to(ROOT))
        original = path.read_bytes()
        saved = CHECKPOINT / relative.replace("/", "__")
        saved.write_bytes(original)
        saved.chmod(0o600)
        evidence["files"][relative] = {"before": sha(original), "after": sha(candidate)}
    (CHECKPOINT / "manifest.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (CHECKPOINT / "manifest.json").chmod(0o600)
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, candidate in candidates.items():
            atomic_write(path, candidate)
        for path, candidate in candidates.items():
            if sha(path.read_bytes()) != sha(candidate):
                raise RuntimeError("repin verification failed: " + str(path))
    except Exception:
        for path in candidates:
            saved = CHECKPOINT / str(path.relative_to(ROOT)).replace("/", "__")
            atomic_write(path, saved.read_bytes())
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "player_pin": player_pin, "reader_pin": reader_pin,
                      "family_sha256": sha(family)}, sort_keys=True))


if __name__ == "__main__":
    main()
