"""Create a bounded, non-secret inventory of an AsterTV release candidate.

Only explicitly listed JSON anchors are inspected.  Their bytes are hashed,
but their contents are never copied into the report.  The tiny allowlist of
metadata fields is descriptive; all other values remain source-local.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath


MAX_ANCHOR_BYTES = 1024 * 1024
DENIED_PARTS = {
    "credential", "credentials", "secret", "secrets", "token", "tokens",
    "api_keys.json", "password", "passwords", "userdata", "database",
    "databases", "profiles", "watch-history", "listening-progress",
}


class InventoryError(ValueError):
    pass


def require(value: object, code: str) -> None:
    if not value:
        raise InventoryError(code)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_absolute(value: object) -> PurePosixPath:
    require(isinstance(value, str) and value.startswith("/"),
            "inventory-anchor-path")
    path = PurePosixPath(value)
    require(".." not in path.parts and path.as_posix() == value,
            "inventory-anchor-path")
    lowered = {part.lower() for part in path.parts}
    require(not lowered.intersection(DENIED_PARTS),
            "inventory-anchor-denied")
    return path


def local_path(root: Path, absolute: PurePosixPath) -> Path:
    return root.joinpath(*absolute.parts[1:])


def read_anchor(root: Path, component: dict) -> tuple[dict, dict]:
    name = component.get("name")
    require(isinstance(name, str) and name and len(name) <= 80,
            "inventory-component-name")
    absolute = safe_absolute(component.get("path"))
    path = local_path(root, absolute)
    try:
        info = path.lstat()
    except FileNotFoundError:
        if component.get("required", True):
            raise InventoryError("inventory-required-anchor-missing") from None
        return ({"name": name, "path": absolute.as_posix(),
                 "required": False, "status": "missing"}, {})
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink(),
            "inventory-anchor-not-regular")
    require(0 < info.st_size <= MAX_ANCHOR_BYTES,
            "inventory-anchor-size")
    raw = path.read_bytes()
    require(len(raw) == info.st_size, "inventory-anchor-raced")
    digest = sha256(raw)
    expected = component.get("sha256")
    require(isinstance(expected, str) and len(expected) == 64,
            "inventory-anchor-pin")
    require(digest == expected, "inventory-anchor-drift")
    anchor_format = component.get("format", "json")
    require(anchor_format in ("json", "opaque"), "inventory-anchor-format")
    value = {}
    if anchor_format == "json":
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise InventoryError("inventory-anchor-json") from None
        require(isinstance(value, dict), "inventory-anchor-object")
    expected_kind = component.get("kind")
    if expected_kind is not None:
        require(anchor_format == "json", "inventory-anchor-metadata-format")
        require(value.get("kind") == expected_kind,
                "inventory-anchor-kind")
    expected_schema = component.get("schema")
    if expected_schema is not None:
        require(anchor_format == "json", "inventory-anchor-metadata-format")
        require(value.get("schema") == expected_schema,
                "inventory-anchor-schema")
    row = {
        "name": name,
        "path": absolute.as_posix(),
        "required": bool(component.get("required", True)),
        "status": "verified",
        "sha256": digest,
        "bytes": len(raw),
        "format": anchor_format,
    }
    if expected_kind is not None:
        row["kind"] = expected_kind
    if expected_schema is not None:
        row["schema"] = expected_schema
    return row, value


def field(value: dict, dotted: object) -> object:
    require(isinstance(dotted, str) and dotted and len(dotted) <= 160,
            "inventory-relation-field")
    current: object = value
    for part in dotted.split("."):
        require(part and part not in ("__class__", "__dict__"),
                "inventory-relation-field")
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def build(spec: dict, root: Path = Path("/")) -> dict:
    require(isinstance(spec, dict) and spec.get("schema") == 1
            and spec.get("kind") == "aster-release-inventory-spec.v1",
            "inventory-spec")
    components = spec.get("components")
    require(isinstance(components, list) and 1 <= len(components) <= 64,
            "inventory-components")
    rows: list[dict] = []
    parsed: dict[str, dict] = {}
    digests: dict[str, str] = {}
    for component in components:
        require(isinstance(component, dict), "inventory-component")
        row, value = read_anchor(root, component)
        require(row["name"] not in parsed and row["name"] not in digests,
                "inventory-component-duplicate")
        rows.append(row)
        if row["status"] == "verified":
            parsed[row["name"]] = value
            digests[row["name"]] = row["sha256"]

    relations = spec.get("relations", [])
    require(isinstance(relations, list) and len(relations) <= 64,
            "inventory-relations")
    relation_rows = []
    complete = True
    recovery_complete = True
    for relation in relations:
        require(isinstance(relation, dict), "inventory-relation")
        name = relation.get("name")
        source = relation.get("source")
        target = relation.get("target")
        require(isinstance(name, str) and name and len(name) <= 100,
                "inventory-relation-name")
        require(source in parsed and target in digests,
                "inventory-relation-component")
        matches = field(parsed[source], relation.get("field")) == digests[target]
        required = bool(relation.get("required", True))
        relation_rows.append({"name": name, "required": required,
                              "recovery": bool(relation.get("recovery", False)),
                              "status": "matched" if matches else "stale"})
        if required and not matches:
            complete = False
        if relation.get("recovery", False) and not matches:
            recovery_complete = False

    if any(row["required"] and row["status"] != "verified" for row in rows):
        complete = False
    return {
        "schema": 1,
        "kind": "aster-release-inventory.v1",
        "candidate": spec.get("candidate", "AsterTV v2 HP"),
        "complete": complete,
        "recovery_complete": recovery_complete,
        "components": rows,
        "relations": relation_rows,
        "excluded": [
            "credentials", "user profiles", "watch history",
            "listening progress", "media databases", "cached media",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("--root", type=Path, default=Path("/"))
    args = parser.parse_args()
    spec = json.loads(args.spec.read_bytes())
    print(json.dumps(build(spec, args.root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
