"""Hash-only client token registry for the podcast queue."""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
import stat

from contract import Identity


class AuthenticationError(ValueError):
    pass


class TokenRegistry:
    def __init__(self, path: Path):
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_nlink != 1
                or info.st_mode & 0o077 or info.st_size > 64 * 1024):
            raise AuthenticationError("token-registry-custody")
        value = json.loads(path.read_text())
        if (not isinstance(value, dict) or set(value) != {"schema", "clients"}
                or value["schema"] != "aster-podcast-client-tokens.v1"
                or not isinstance(value["clients"], list) or len(value["clients"]) > 16):
            raise AuthenticationError("token-registry-schema")
        self.records: list[tuple[str, Identity]] = []
        for record in value["clients"]:
            if not isinstance(record, dict) or set(record) != {
                "token_sha256", "client_id", "profile_id", "enabled"
            } or type(record["enabled"]) is not bool:
                raise AuthenticationError("token-record-schema")
            digest = record["token_sha256"]
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(char not in "0123456789abcdef" for char in digest)):
                raise AuthenticationError("token-digest")
            if record["enabled"]:
                self.records.append((digest, Identity(record["client_id"], record["profile_id"])))

    def authenticate(self, header: object) -> Identity:
        if (not isinstance(header, str) or not header.startswith("Bearer ")
                or not 32 <= len(header[7:]) <= 256 or any(char.isspace() for char in header[7:])):
            raise AuthenticationError("unauthorized")
        digest = hashlib.sha256(header[7:].encode()).hexdigest()
        matches = [identity for expected, identity in self.records
                   if hmac.compare_digest(digest, expected)]
        if len(matches) != 1:
            raise AuthenticationError("unauthorized")
        return matches[0]
