#!/usr/bin/env python3
"""Install the accepted-release guard on the AsterTV-Jen test client."""

import importlib.util
from pathlib import Path


RELIABILITY = Path(__file__).resolve().parents[1] / "reliability" / "install.py"
EXPECTED_INSTALLER_SHA256 = (
    "f6511d18511849e0d22a8a8cb0335deeeb521c15ad30a396ce13feb4371be93d"
)


def main() -> None:
    import hashlib

    if hashlib.sha256(RELIABILITY.read_bytes()).hexdigest() != EXPECTED_INSTALLER_SHA256:
        raise SystemExit("reliability-installer-drift")
    spec = importlib.util.spec_from_file_location("astertv_reliability_install", RELIABILITY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.ALLOWED_HOSTS = {"AsterTV-Jen"}
    # The accepted v2.0.7 archive predates plugin.video.astersearch. Production
    # gained that v3-alpha component later, so a clean v2 client must explicitly
    # omit it until a v3 candidate is accepted and the baseline is refreshed.
    module.SNAPSHOT_EXTRA_ARGS = (
        "--allow-missing-guarded", "plugin.video.astersearch")
    module.main()


if __name__ == "__main__":
    main()
