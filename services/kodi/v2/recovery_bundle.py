"""Assemble exact, non-secret AsterTV recovery sources into one directory."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil

from release_inventory import InventoryError, require


MAX_FILES = 4096
MAX_BYTES = 128 * 1024 * 1024
SKIP_NAMES = {"deploy.lock", ".DS_Store", "search-proof.png",
              "youtube-landing.png"}
SKIP_SUFFIXES = (".pyc", ".pyo")
DENIED_NAMES = {"api_keys.json", "guisettings.xml", "Addons33.db"}
SKIP_LINKS = {"data"}  # compiled-reader publication mount, never client recovery data


def stage_path(value: object) -> PurePosixPath:
    require(isinstance(value, str)
            and value.startswith("/storage/.aster-staging/")
            and ".." not in value.split("/"), "bundle-source-path")
    return PurePosixPath(value)


def transient(relative: Path) -> bool:
    return ("__pycache__" in relative.parts
            or any(part.startswith("._") for part in relative.parts)
            or relative.name in SKIP_NAMES
            or relative.name.startswith("result-")
            or relative.name.startswith("deploy-")
            or relative.name.endswith(SKIP_SUFFIXES))


def members(root: Path, absolute: PurePosixPath) -> tuple[list[dict], int, str]:
    source = root.joinpath(*absolute.parts[1:])
    require(source.is_dir() and not source.is_symlink(), "bundle-source")
    rows = []
    total = 0
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_symlink() and relative.as_posix() in SKIP_LINKS:
            continue
        require(not path.is_symlink(), "bundle-linked-member")
        if path.is_dir():
            continue
        require(path.is_file(), "bundle-special-member")
        if transient(relative):
            continue
        require(relative.name not in DENIED_NAMES, "bundle-private-member")
        raw = path.read_bytes()
        total += len(raw)
        require(len(rows) < MAX_FILES and total <= MAX_BYTES,
                "bundle-source-bounds")
        rows.append({"path": relative.as_posix(), "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest()})
    require(rows, "bundle-empty-source")
    encoded = b"".join((row["path"] + "\0" + str(row["bytes"]) + "\0"
                        + row["sha256"] + "\n").encode() for row in rows)
    return rows, total, hashlib.sha256(encoded).hexdigest()


def audit(plan: dict, root: Path = Path("/")) -> list[dict]:
    sources = plan.get("sources")
    require(isinstance(sources, list) and 1 <= len(sources) <= 64,
            "bundle-sources")
    result = []
    seen = set()
    for source in sources:
        require(isinstance(source, dict), "bundle-source-row")
        absolute = stage_path(source.get("path"))
        require(absolute.as_posix() not in seen, "bundle-source-duplicate")
        expected = source.get("tree_sha256")
        require(isinstance(expected, str) and len(expected) == 64,
                "bundle-source-pin")
        rows, size, digest = members(root, absolute)
        require(digest == expected, "bundle-source-drift")
        seen.add(absolute.as_posix())
        result.append({"path": absolute.as_posix(), "tree_sha256": digest,
                       "files": len(rows), "bytes": size})
    return result


def build(plan: dict, root: Path, output: Path) -> str:
    require(not output.exists(), "bundle-output-exists")
    audited = audit(plan, root)
    output.mkdir(parents=True, mode=0o700)
    source_root = output / "sources"
    file_rows = []
    for summary in audited:
        absolute = stage_path(summary["path"])
        source = root.joinpath(*absolute.parts[1:])
        name = absolute.name
        rows, _, _ = members(root, absolute)
        for row in rows:
            src = source / row["path"]
            dst = source_root / name / row["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            dst.chmod(0o600)
            require(hashlib.sha256(dst.read_bytes()).hexdigest() == row["sha256"],
                    "bundle-copy-drift")
            file_rows.append({"source": name, **row})
    manifest = {"schema": 1, "kind": "aster-recovery-bundle.v1",
                "sources": audited, "files": file_rows,
                "excludes": ["credentials", "profiles", "history",
                             "listening progress", "databases", "result logs",
                             "locks", "proof screenshots", "bytecode"]}
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    (output / "manifest.json").write_bytes(raw)
    (output / "manifest.json").chmod(0o600)
    return hashlib.sha256(raw).hexdigest()


def verify(bundle: Path, expected_pin: str) -> dict:
    require(bundle.is_dir() and not bundle.is_symlink(), "bundle-verify-root")
    manifest_path = bundle / "manifest.json"
    require(manifest_path.is_file() and not manifest_path.is_symlink(),
            "bundle-verify-manifest")
    raw = manifest_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_pin,
            "bundle-verify-pin")
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise InventoryError("bundle-verify-json") from None
    require(manifest.get("schema") == 1
            and manifest.get("kind") == "aster-recovery-bundle.v1",
            "bundle-verify-contract")
    expected = {"manifest.json"}
    grouped: dict[str, list[dict]] = {}
    for row in manifest.get("files", []):
        require(isinstance(row, dict), "bundle-verify-row")
        source = row.get("source"); relative = row.get("path")
        require(isinstance(source, str) and "/" not in source
                and isinstance(relative, str) and relative
                and ".." not in relative.split("/"), "bundle-verify-path")
        path = bundle / "sources" / source / relative
        require(path.is_file() and not path.is_symlink(), "bundle-verify-file")
        file_raw = path.read_bytes()
        require(len(file_raw) == row.get("bytes")
                and hashlib.sha256(file_raw).hexdigest() == row.get("sha256"),
                "bundle-verify-drift")
        expected.add(path.relative_to(bundle).as_posix())
        grouped.setdefault(source, []).append(row)
    for summary in manifest.get("sources", []):
        name = PurePosixPath(summary["path"]).name
        rows = sorted(grouped.get(name, []), key=lambda row: row["path"])
        encoded = b"".join((row["path"] + "\0" + str(row["bytes"]) + "\0"
                            + row["sha256"] + "\n").encode() for row in rows)
        require(len(rows) == summary.get("files")
                and sum(row["bytes"] for row in rows) == summary.get("bytes")
                and hashlib.sha256(encoded).hexdigest() == summary.get("tree_sha256"),
                "bundle-verify-tree")
    actual = {path.relative_to(bundle).as_posix() for path in bundle.rglob("*")
              if path.is_file()}
    require(actual == expected, "bundle-verify-extra")
    return {"verified": True, "sources": len(manifest["sources"]),
            "files": len(manifest["files"]),
            "bytes": sum(row["bytes"] for row in manifest["files"])}
