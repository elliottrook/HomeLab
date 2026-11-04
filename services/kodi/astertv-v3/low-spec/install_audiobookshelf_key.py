#!/usr/bin/env python3
"""Install a newly-issued Audiobookshelf API key on AsterTV-Jen."""

import hashlib
import json
import os
from pathlib import Path
import socket


SOURCE = Path("/storage/.aster-staging/astertv-jen-api-key.json")
PROFILE = Path("/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks")
CLIENT = PROFILE / "client.json"
MARKER = PROFILE / "progress-enabled.json"
SERVER = "https://audiobooks.elliottrook.com"


def main() -> None:
    if socket.gethostname() != "AsterTV-Jen" or os.getuid() != 0:
        raise SystemExit("AsterTV-Jen-root-only")
    if CLIENT.exists() or MARKER.exists() or not SOURCE.is_file() or SOURCE.is_symlink():
        raise RuntimeError("audiobookshelf-install-state")
    issued = json.loads(SOURCE.read_text())
    key = issued.get("api_key")
    if (issued.get("name") != "AsterTV-Jen" or issued.get("username") != "jason"
            or not isinstance(key, str) or len(key) < 32 or any(c.isspace() for c in key)):
        raise RuntimeError("audiobookshelf-key-schema")
    PROFILE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(PROFILE, 0o700)
    for path, value in (
        (CLIENT, {"server_url": SERVER, "api_key": key}),
        (MARKER, {"enabled": True, "host": "AsterTV-Jen",
                  "account_sha256": issued["user_id_sha256"],
                  "kind": "aster-books-sync-pilot.v1"}),
    ):
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(path, 0o600)
    SOURCE.unlink()
    print(json.dumps({"installed": True, "name": issued["name"],
                      "key_id": issued["key_id"], "credential_output": False,
                      "token_sha256": hashlib.sha256(key.encode()).hexdigest()},
                     sort_keys=True))


if __name__ == "__main__":
    main()
