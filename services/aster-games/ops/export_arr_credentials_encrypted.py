#!/usr/bin/env python3
"""Run on TrueNAS to encrypt ARR credentials to the Aster Games LXC key."""

from __future__ import annotations

import configparser
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def config_mount(container: str) -> Path:
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "--format",
            '{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}',
            container,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    path = Path(result.stdout.strip())
    if not path.is_dir():
        raise RuntimeError(f"{container} /config mount was not resolved")
    return path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} PUBLIC_KEY OUTPUT", file=sys.stderr)
        return 2
    public_key = Path(sys.argv[1])
    output = Path(sys.argv[2])
    if not public_key.is_file():
        raise RuntimeError("recipient public key is unavailable")
    if output.exists():
        raise RuntimeError("refusing to replace encrypted credential bundle")

    prowlarr_root = ET.parse(config_mount("prowlarr") / "config.xml").getroot()
    prowlarr_key = (prowlarr_root.findtext("ApiKey") or "").strip()

    sab_config = configparser.ConfigParser(interpolation=None)
    sab_text = (config_mount("sabnzbd") / "sabnzbd.ini").read_text(encoding="utf-8")
    first_section = sab_text.find("[")
    if first_section < 0:
        raise RuntimeError("SABnzbd configuration has no INI sections")
    sab_config.read_string(sab_text[first_section:])
    sab_key = sab_config.get("misc", "api_key", fallback="").strip()

    if len(prowlarr_key) < 20 or len(sab_key) < 20:
        raise RuntimeError("one or more ARR credentials failed validation")

    payload = json.dumps(
        {"PROWLARR_API_KEY": prowlarr_key, "SABNZBD_API_KEY": sab_key},
        separators=(",", ":"),
    ).encode()
    if len(payload) > 250:
        raise RuntimeError("credential payload exceeds the RSA-OAEP envelope")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="aster-games-arr-", delete=False) as handle:
        plaintext = Path(handle.name)
        handle.write(payload)
    try:
        os.chmod(plaintext, 0o600)
        subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-encrypt",
                "-pubin",
                "-inkey",
                str(public_key),
                "-in",
                str(plaintext),
                "-out",
                str(output),
                "-pkeyopt",
                "rsa_padding_mode:oaep",
                "-pkeyopt",
                "rsa_oaep_md:sha256",
            ],
            check=True,
        )
        os.chmod(output, 0o600)
    finally:
        plaintext.unlink(missing_ok=True)

    print(f"encrypted two validated ARR credentials to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
