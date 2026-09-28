#!/usr/bin/env python3
"""Validate and sanitize a bounded B60 kernel-log excerpt."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MAX_LINES = 500
MAX_LINE_LENGTH = 2000
RELEVANT = re.compile(r"(?i)\b(xe|drm|oom|out of memory|device.{0,20}lost|reset|hang)\b")
SECRET = re.compile(r"(?i)(authorization:|bearer\s+|api[_-]?key|password|secret|token=|private key)")
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class KernelLogError(ValueError):
    pass


def sanitize(text: str) -> str:
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        raise KernelLogError(f"excerpt exceeds {MAX_LINES} lines")
    clean = []
    for number, line in enumerate(lines, 1):
        if len(line) > MAX_LINE_LENGTH:
            raise KernelLogError(f"line {number} exceeds length limit")
        if CONTROL.search(line) or SECRET.search(line):
            raise KernelLogError(f"line {number} contains unsafe text")
        if not RELEVANT.search(line):
            raise KernelLogError(f"line {number} is outside the B60 failure allowlist")
        clean.append(line.rstrip())
    return "\n".join(clean) + ("\n" if clean else "")


def classify(text: str) -> list[str]:
    lowered = text.lower()
    findings = []
    for name, pattern in (
        ("kernel_oom", r"oom|out of memory"),
        ("gpu_reset", r"\breset\b"),
        ("device_loss", r"device.{0,20}lost"),
        ("gpu_hang", r"\bhang\b"),
    ):
        if re.search(pattern, lowered):
            findings.append(name)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        result = sanitize(args.path.read_text(encoding="utf-8"))
    except (OSError, KernelLogError) as exc:
        print(f"invalid kernel log: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(result)
    return 1 if classify(result) else 0


if __name__ == "__main__":
    raise SystemExit(main())
