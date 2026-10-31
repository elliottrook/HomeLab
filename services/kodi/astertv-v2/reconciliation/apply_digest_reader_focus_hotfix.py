#!/usr/bin/env python3
"""One-time upgrade from the first r10 repin to robust Digest reader focus."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile


ROOT = Path("/storage/.kodi/addons")
READER = ROOT / "script.asterruntime/aster-digest-reader6"
DEFAULT = READER / "default.py"
MANIFEST = READER / "manifest.json"
DIGEST = ROOT / "skin.asterhome/1080i/custom_1111_digest.xml"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-r10-digest-focus-20261030")
EXPECTED = {
    DEFAULT: "ab4cc088c9cec9ddea759243a1b13210134a1a4ff0bb7c6426e57642c0cfc8d0",
    MANIFEST: "ffce6627d25052d162362b6b02c11a5c71d864c2a51895472e699cb758be6c18",
    DIGEST: "b52ec2a5c6187038d9991746ddff2a3cfa2487f1ef17d775c02cfa2a957c04d7",
    FAMILY: "118d25418c2698386f77723b5d75f7510f251f369133c6047f88867aba91c390",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def replace_once(data, old, new):
    text = data.decode()
    if text.count(old) != 1:
        raise RuntimeError("digest focus replacement count")
    return text.replace(old, new, 1).encode()


def atomic_write(path, data):
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-digest-focus-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o644); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def no_player():
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + "\n").encode())
        if json.loads(client.recv(4096)).get("result") != []:
            raise RuntimeError("active player")


def main():
    if os.uname().nodename != "AsterTV" or CHECKPOINT.exists():
        raise RuntimeError("lab/checkpoint guard")
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected r10 member: " + str(path))
    no_player()
    reader = replace_once(
        originals[DEFAULT],
        """def context(args, window, focus, ready):
""",
        """def focused_control(window, window_id):
    try:
        reported = window.getFocusId()
    except RuntimeError:
        reported = 0
    if reported:
        return reported
    if window_id == 11111:
        for control_id in (312, 310, 311, 301, 305, 300, 302, 304, 303, 500):
            if xbmc.getCondVisibility('Control.HasFocus(' + str(control_id) + ')'):
                return control_id
    return reported

def context(args, window, focus, ready):
""",
    )
    reader = replace_once(reader, "source_focus = source.getFocusId()",
                          "source_focus = focused_control(source, source_id)")
    reader = replace_once(
        reader,
        "not window_active(source_id) or source.getFocusId() != source_focus",
        "not window_active(source_id) or focused_control(source, source_id) != source_focus",
    )
    if sha(reader) != "32c5b955ee6551d3a9673889dabe2d421352274946ceaf5ce9aeb0bbcb37d1c0":
        raise RuntimeError("digest reader candidate mismatch")
    manifest = json.loads(originals[MANIFEST])
    row = next(row for row in manifest["files"] if row["path"] == "default.py")
    row["bytes"] = len(reader); row["sha256"] = sha(reader)
    manifest_data = encode(manifest); reader_pin = sha(manifest_data)
    digest = replace_once(originals[DIGEST], EXPECTED[MANIFEST], reader_pin)
    family = json.loads(originals[FAMILY])
    family["components"]["aster-digest-reader6"]["manifest_sha256"] = reader_pin
    family["skin"]["1080i/custom_1111_digest.xml"] = sha(digest)
    family_data = encode(family)
    candidates = {DEFAULT: reader, MANIFEST: manifest_data, DIGEST: digest, FAMILY: family_data}
    CHECKPOINT.mkdir(mode=0o700)
    for path, data in originals.items():
        saved = CHECKPOINT / str(path.relative_to(ROOT)).replace("/", "__")
        saved.write_bytes(data); saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-r10-digest-focus",
        "files": {str(path.relative_to(ROOT)): {"before": sha(originals[path]),
                                                   "after": sha(candidates[path])}
                  for path in candidates}}, indent=2, sort_keys=True) + "\n")
    (CHECKPOINT / "manifest.json").chmod(0o600)
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, data in candidates.items(): atomic_write(path, data)
        for path, data in candidates.items():
            if sha(path.read_bytes()) != sha(data): raise RuntimeError("install verification")
    except Exception:
        for path, data in originals.items(): atomic_write(path, data)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "reader_pin": reader_pin,
                      "family_sha256": sha(family_data), "checkpoint": str(CHECKPOINT)},
                     sort_keys=True))


if __name__ == "__main__": main()
