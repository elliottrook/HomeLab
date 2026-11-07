#!/usr/bin/env python3
"""Apply source-local credentials to ROMarr without printing their values."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def replace_env(path: Path, replacements: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in replacements:
            output.append(f"{key}={replacements[key]}")
            seen.add(key)
        else:
            output.append(line)
    missing = set(replacements) - seen
    if missing:
        raise RuntimeError(f"environment is missing required keys: {sorted(missing)}")
    atomic_write(path, "\n".join(output) + "\n", 0o600)


def atomic_write(path: Path, content: str, mode: int) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def one(entries: list[dict], entry_type: str) -> dict:
    matches = [entry for entry in entries if entry.get("type") == entry_type]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {entry_type} entry")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--encrypted", required=True, type=Path)
    parser.add_argument("--private-key", required=True, type=Path)
    parser.add_argument("--romm-token", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--env", required=True, type=Path)
    parser.add_argument("--enable-acquisition", action="store_true")
    args = parser.parse_args()

    with tempfile.NamedTemporaryFile(prefix="aster-games-arr-", delete=False) as handle:
        plaintext = Path(handle.name)
    try:
        import subprocess

        subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-decrypt",
                "-inkey",
                str(args.private_key),
                "-in",
                str(args.encrypted),
                "-out",
                str(plaintext),
                "-pkeyopt",
                "rsa_padding_mode:oaep",
                "-pkeyopt",
                "rsa_oaep_md:sha256",
            ],
            check=True,
        )
        credentials = json.loads(plaintext.read_text(encoding="utf-8"))
    finally:
        plaintext.unlink(missing_ok=True)

    for key in ("PROWLARR_API_KEY", "SABNZBD_API_KEY"):
        if not isinstance(credentials.get(key), str) or len(credentials[key]) < 20:
            raise RuntimeError(f"decrypted {key} failed validation")
    romm_token = args.romm_token.read_text(encoding="utf-8").strip()
    if len(romm_token) < 20:
        raise RuntimeError("RomM token failed validation")

    original_config = args.config.read_text(encoding="utf-8")
    document = json.loads(original_config)
    settings = document["settings"]
    library = one(settings["libraries"], "romm")
    indexer = one(settings["indexers"], "prowlarr")
    downloader = one(settings["download_clients"], "sabnzbd")

    library.update(api_key=romm_token, enable=True, path="/roms")
    indexer.update(api_key=credentials["PROWLARR_API_KEY"], enable=args.enable_acquisition)
    downloader.update(
        api_key=credentials["SABNZBD_API_KEY"],
        enable=args.enable_acquisition,
        category="retro-games",
    )
    settings["auto_import"] = args.enable_acquisition
    settings["rescan_after_import"] = True

    backup = args.config.with_suffix(".json.pre-arr-integration")
    if backup.exists():
        raise RuntimeError("ROMarr integration backup already exists")
    atomic_write(backup, original_config, 0o600)
    atomic_write(args.config, json.dumps(document, indent=2, sort_keys=True) + "\n", 0o600)
    replace_env(
        args.env,
        {
            "PROWLARR_API_KEY": credentials["PROWLARR_API_KEY"],
            "SABNZBD_API_KEY": credentials["SABNZBD_API_KEY"],
            "ROMM_ROMARR_API_KEY": romm_token,
        },
    )
    print(
        "configured ROMarr credentials; "
        f"acquisition_enabled={args.enable_acquisition} category=retro-games"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
