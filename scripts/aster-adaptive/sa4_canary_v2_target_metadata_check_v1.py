"""Fixed metadata check for the accepted SA4 v2 canary."""
from __future__ import annotations

import hashlib

import sa4_single_file_repair_contract_v1 as contract


EXPECTED_SHA256 = "fae178a1558199b66f4dc9abec18690ed22a7cbee398f411b47f93daf1d3a0c2"
FIELDS = {"device", "inode", "uid", "gid", "mode", "link_count", "size",
          "regular_file", "symlink", "bytes_sha256"}


def check(value: object) -> dict[str, object]:
    if (not isinstance(value, dict) or set(value) != FIELDS
            or type(value["device"]) is not int or value["device"] <= 0
            or type(value["inode"]) is not int or value["inode"] <= 0
            or value["uid"] != 0 or value["gid"] != 0
            or value["mode"] != "0644" or value["link_count"] != 1
            or value["size"] != 85 or value["regular_file"] is not True
            or value["symlink"] is not False
            or value["bytes_sha256"] != EXPECTED_SHA256):
        raise ValueError("SA4 v2 canary metadata changed")
    return {"schema": "aster-sa4-canary-v2-metadata-check.v1",
            "state": "pass", "measurement_sha256": hashlib.sha256(
                contract.canonical(value)).hexdigest(),
            "effects": 0, "authority": "none"}
