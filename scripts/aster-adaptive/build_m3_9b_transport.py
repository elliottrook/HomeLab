"""Emit a single stdin-only program with the pinned synthetic fixture embedded."""
import base64
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "m3_9b_sycl_compat.py"
FIXTURE = HERE / "fixtures/routing-families-v1.json"
EXPECTED = "c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec"


def main():
    fixture = FIXTURE.read_bytes()
    if hashlib.sha256(fixture).hexdigest() != EXPECTED:
        raise SystemExit("fixture digest mismatch")
    sys.stdout.write("FROZEN_FIXTURE_B64 = " + repr(base64.b64encode(fixture).decode()) + "\n")
    sys.stdout.write(SOURCE.read_text())


if __name__ == "__main__":
    main()
