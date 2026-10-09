"""Create and verify deterministic SHA-256 manifests without exposing assets."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path


def entries(root: Path) -> list[tuple[str, str]]:
    output = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        output.append((sha256(path.read_bytes()).hexdigest(), path.relative_to(root).as_posix()))
    return output


def render(root: Path) -> str:
    return "".join(f"{digest}  {name}\n" for digest, name in entries(root))


def verify(root: Path, manifest: Path) -> list[str]:
    expected = manifest.read_text(encoding="utf-8")
    actual = render(root)
    if expected == actual:
        return []
    expected_lines = set(expected.splitlines())
    actual_lines = set(actual.splitlines())
    return ([f"missing or changed: {line}" for line in sorted(expected_lines - actual_lines)] +
            [f"unexpected or changed: {line}" for line in sorted(actual_lines - expected_lines)])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        problems = verify(args.root, args.verify)
        for problem in problems:
            print(problem)
        return int(bool(problems))
    print(render(args.root), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
