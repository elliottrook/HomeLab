#!/usr/bin/env python3
"""Install the single-use staged podcast broker identity on AsterTV-Jen."""

import json
import os
from pathlib import Path
import socket


SOURCE = Path("/storage/.aster-staging/aster-podcast-request-client.json")
ROOT = Path("/storage/.kodi/userdata/addon_data/script.astertv.podcast.requests")
TARGET = ROOT / "client.json"


def main() -> None:
    if socket.gethostname() != "AsterTV-Jen" or os.getuid() != 0:
        raise SystemExit("AsterTV-Jen-root-only")
    if TARGET.exists() or not SOURCE.is_file() or SOURCE.is_symlink():
        raise RuntimeError("podcast-client-install-state")
    value = json.loads(SOURCE.read_text())
    if (set(value) != {"schema", "server_url", "token", "client_id", "profile_id"}
            or value["schema"] != "aster-podcast-request-client.v1"
            or value["server_url"] != "http://192.168.20.40:8790"
            or value["client_id"] != "AsterTV-Jen" or value["profile_id"] != "jason"
            or not isinstance(value["token"], str) or not 32 <= len(value["token"]) <= 256
            or any(char.isspace() for char in value["token"])):
        raise RuntimeError("podcast-client-schema")
    ROOT.mkdir(mode=0o700, parents=True)
    os.chmod(ROOT, 0o700)
    descriptor = os.open(TARGET, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(TARGET, 0o600)
    SOURCE.unlink()
    print(json.dumps({"installed": True, "client_id": value["client_id"],
                      "profile_id": value["profile_id"],
                      "credential_output": False}, sort_keys=True))


if __name__ == "__main__":
    main()
