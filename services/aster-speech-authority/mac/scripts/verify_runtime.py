#!/usr/bin/env python3
"""Fail closed unless the Mac speech binaries have a durable local runtime."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


RUNTIMES = {
    "tts-server": {
        "directory": "qwen",
        "rpath": "@loader_path/../lib/qwen",
        "libraries": {
            "libggml.0.dylib",
            "libggml-base.0.dylib",
            "libggml-blas.0.dylib",
            "libggml-cpu.0.dylib",
            "libggml-metal.0.dylib",
        },
    },
    "whisper-server": {
        "directory": "whisper",
        "rpath": "@loader_path/../lib/whisper",
        "libraries": {
            "libwhisper.1.dylib",
            "libggml.0.dylib",
            "libggml-base.0.dylib",
            "libggml-blas.0.dylib",
            "libggml-cpu.0.dylib",
            "libggml-metal.0.dylib",
        },
    },
}


class RuntimeVerificationError(RuntimeError):
    pass


def _otool(arguments: list[str], path: Path) -> str:
    result = subprocess.run(
        ["/usr/bin/otool", *arguments, str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _rpaths(path: Path) -> list[str]:
    lines = _otool(["-l"], path).splitlines()
    values: list[str] = []
    for index, line in enumerate(lines):
        if line.strip() == "cmd LC_RPATH":
            for candidate in lines[index + 1 : index + 5]:
                stripped = candidate.strip()
                if stripped.startswith("path "):
                    values.append(stripped.split(" ", 2)[1])
                    break
    return values


def _dependencies(path: Path) -> list[str]:
    lines = _otool(["-L"], path).splitlines()[1:]
    return [line.strip().split(" (", 1)[0] for line in lines if line.strip()]


def _verify_file(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise RuntimeVerificationError(f"runtime file must be a regular file: {path}")


def verify(root: Path) -> None:
    for binary_name, contract in RUNTIMES.items():
        binary = root / "bin" / binary_name
        library_root = root / "lib" / str(contract["directory"])
        expected_libraries = set(contract["libraries"])
        _verify_file(binary)
        if _rpaths(binary) != [contract["rpath"]]:
            raise RuntimeVerificationError(f"unexpected runtime path for {binary_name}")

        actual_libraries = {item.name for item in library_root.iterdir()}
        if actual_libraries != expected_libraries:
            raise RuntimeVerificationError(f"unexpected library set for {binary_name}")
        for library_name in sorted(expected_libraries):
            _verify_file(library_root / library_name)

        for inspected in [binary, *(library_root / name for name in expected_libraries)]:
            for dependency in _dependencies(inspected):
                if dependency.startswith("@rpath/"):
                    name = dependency.removeprefix("@rpath/")
                    if name not in expected_libraries:
                        raise RuntimeVerificationError(
                            f"unbundled dependency for {binary_name}: {dependency}"
                        )
                elif not dependency.startswith(("/usr/lib/", "/System/Library/")):
                    raise RuntimeVerificationError(
                        f"external dependency for {binary_name}: {dependency}"
                    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    verify(args.root.resolve())
    print("durable speech runtime verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
