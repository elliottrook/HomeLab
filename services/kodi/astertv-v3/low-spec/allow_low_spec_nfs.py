#!/usr/bin/env python3
"""Add AsterTV-Jen to the two read-only AsterReader NFS shares."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess


CHECKPOINT = Path(
    "/mnt/Media/appdata/unified-media-shadow/checkpoints/astertv-jen-nfs-20261104.json"
)
TARGET = "192.168.1.180"
EXPECTED = {
    10: "/mnt/Media/AsterReader/ready",
    11: "/mnt/Media/AsterReader/generations",
}
PREDECESSORS = ["192.168.1.140", "192.168.1.157"]


def call(*arguments: str):
    reply = subprocess.run(
        ["midclt", "call", *arguments], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
    )
    return json.loads(reply.stdout or b"null")


def main() -> None:
    if os.getuid() != 0 or CHECKPOINT.exists():
        raise RuntimeError("low-spec-nfs-install-state")
    shares = {row["id"]: row for row in call("sharing.nfs.query")}
    before = {}
    for identity, path in EXPECTED.items():
        row = shares[identity]
        if (row.get("path") != path or row.get("hosts") != PREDECESSORS
                or row.get("networks") != [] or row.get("ro") is not True
                or row.get("enabled") is not True):
            raise RuntimeError("low-spec-nfs-predecessor-drift")
        before[identity] = {"hosts": row["hosts"], "path": row["path"],
                            "ro": row["ro"], "enabled": row["enabled"]}
    CHECKPOINT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(CHECKPOINT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(before, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    changed = []
    try:
        for identity in EXPECTED:
            call("sharing.nfs.update", str(identity),
                 json.dumps({"hosts": PREDECESSORS + [TARGET]}))
            changed.append(identity)
    except Exception:
        for identity in changed:
            call("sharing.nfs.update", str(identity),
                 json.dumps({"hosts": PREDECESSORS}))
        raise
    current = {row["id"]: row for row in call("sharing.nfs.query")}
    for identity in EXPECTED:
        if current[identity].get("hosts") != PREDECESSORS + [TARGET]:
            raise RuntimeError("low-spec-nfs-postcondition")
    print(json.dumps({"installed": True, "shares": sorted(EXPECTED),
                      "target": TARGET, "checkpoint": str(CHECKPOINT)}))


if __name__ == "__main__":
    main()
