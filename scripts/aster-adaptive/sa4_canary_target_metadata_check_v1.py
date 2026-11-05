"""Fixed metadata check for the approved SA4 canary target."""
from __future__ import annotations

import hashlib

import sa4_single_file_repair_contract_v1 as contract


FIELDS = {"device", "inode", "uid", "gid", "mode", "link_count", "size",
          "regular_file", "symlink", "bytes_sha256"}


def check(value: object) -> dict[str, object]:
    if (not isinstance(value, dict) or set(value) != FIELDS
            or type(value["device"]) is not int or value["device"] <= 0
            or type(value["inode"]) is not int or value["inode"] <= 0
            or value["uid"] != 0 or value["gid"] != 0
            or value["mode"] != "0644" or value["link_count"] != 1
            or value["size"] != 82 or value["regular_file"] is not True
            or value["symlink"] is not False
            or value["bytes_sha256"]
            != "4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065"):
        raise ValueError("SA4 canary metadata changed")
    return {"schema": "aster-sa4-canary-metadata-check.v1", "state": "pass",
            "measurement_sha256": hashlib.sha256(
                contract.canonical(value)).hexdigest(),
            "effects": 0, "authority": "none"}
