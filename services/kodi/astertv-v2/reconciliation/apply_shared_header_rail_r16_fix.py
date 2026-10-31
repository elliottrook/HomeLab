#!/usr/bin/env python3
"""Normalize the shared Clock/Search/rail treatment on AsterTV v2 lab pages."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

ROOT = Path("/storage/.kodi/addons")
RUNTIME = ROOT / "script.asterruntime"
SKIN = ROOT / "skin.asterhome"
DIGEST = SKIN / "1080i/custom_1111_digest.xml"
BOOKS = SKIN / "1080i/IncludesBooks.xml"
HOME = SKIN / "1080i/Home.xml"
SMART_HOME = SKIN / "1080i/custom_1112_home.xml"
INCLUDES = SKIN / "1080i/Includes.xml"
HUB = SKIN / "1080i/IncludesHub.xml"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-shared-header-rail-r16-20261030")

# Mutated members are hash-gated and checkpointed. Reference members are also
# pinned so the repair cannot silently normalize against a regressed page.
EXPECTED_MUTATED = {
    DIGEST: "c9e13ea968442e1c7bc8c70ae0a0f94bd4e14f5dfbdf2d4198f52da7a7c96bbd",
    BOOKS: "13cbc6bb208f43963b34979028830780c061bf45cc675c86076a92b8b9050995",
    FAMILY: "a172268ee9a22cab7a74babe80378ea1c45952639a5496bbc04097c84e7f541f",
}
EXPECTED_REFERENCE = {
    HOME: "814bb438377ee711e7467c5ef864cdbf1e5c88c2ec4b4e5296eec35c319a3efd",
    SMART_HOME: "18be3ab6b1d4fe5d08b94e9f898d35ac46ce2e7297c4cae0beec3688d4ff7f9f",
    INCLUDES: "4efffe34e841beff8b568c15d268d3e012e486378e88af2b8db8158aac32706a",
    HUB: "74c6d8ee10721bf37750257fee76072f94f16bad4796eafc0de81f0c67baf127",
}

GOLD = "75cbb991"
SEARCH_TRIM = (
    '<control type="image"><left>348</left><top>29</top><width>174</width>'
    '<height>50</height><texture border="18" colordiffuse="75cbb991">'
    'special://skin/media/ui-compact-card-ring.png</texture></control>'
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r16-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_contract(reference: dict[Path, bytes]) -> None:
    home = reference[HOME].decode()
    smart_home = reference[SMART_HOME].decode()
    includes = reference[INCLUDES].decode()
    hub = reference[HUB].decode()
    assert '$INFO[System.Time(HH:mm)]' in includes
    assert includes.count(GOLD) >= 1
    assert hub.count(GOLD) == 2
    assert home.count(SEARCH_TRIM) == 1
    smart_trim = SEARCH_TRIM.replace("<left>348</left>", "<left>441</left>")
    assert smart_home.count(smart_trim) == 1
    for text in (home, smart_home):
        assert text.count('include content="AsterNavigationRail"') == 1
        assert text.count('include content="AsterClockPill"') == 1
        assert text.count('<label>Search</label>') >= 1


def candidates(originals: dict[Path, bytes]) -> dict[Path, bytes]:
    digest_text = originals[DIGEST].decode()
    rail = """    <include content="AsterNavigationRail">
      <param name="content" value="500" />
      <param name="railfocus" value="9003" />
    </include>
"""
    if digest_text.count(rail) != 1:
        raise RuntimeError("News rail source count")
    digest_text = digest_text.replace(rail, "", 1)
    clock = '      <include content="AsterClockPill" />\n'
    if digest_text.count(clock) != 1:
        raise RuntimeError("News clock source count")
    digest_text = digest_text.replace(clock, "", 1)
    if digest_text.count(SEARCH_TRIM) != 1:
        raise RuntimeError("News Search trim source count")
    digest_text = digest_text.replace(SEARCH_TRIM, "", 1)
    marker = """</control>
  </controls>
</window>"""
    if digest_text.count(marker) != 1:
        raise RuntimeError("News controls close marker")
    # Kodi's z-order is not reliably preserved between separate include and
    # content groups. Put the shared chrome last, above the News hero fade.
    topmost = ("</control>\n    " + SEARCH_TRIM + "\n"
               '    <include content="AsterClockPill" />\n' + rail)
    digest_text = digest_text.replace(marker, topmost + "  </controls>\n</window>", 1)
    digest = digest_text.encode()

    books_text = originals[BOOKS].decode()
    old_books_trim = SEARCH_TRIM.replace(GOLD, "ffad8a4d")
    if books_text.count(old_books_trim) != 1:
        raise RuntimeError("Books Search trim source count")
    books_text = books_text.replace(old_books_trim, SEARCH_TRIM, 1)
    books = books_text.encode()

    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/custom_1111_digest.xml"] = sha(digest)
    family["skin"]["1080i/IncludesBooks.xml"] = sha(books)
    return {DIGEST: digest, BOOKS: books, FAMILY: encoded(family)}


def main() -> None:
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    active_players()
    originals = {path: path.read_bytes() for path in EXPECTED_MUTATED}
    reference = {path: path.read_bytes() for path in EXPECTED_REFERENCE}
    for path, expected in {**EXPECTED_MUTATED, **EXPECTED_REFERENCE}.items():
        source = originals.get(path, reference.get(path))
        if source is None or sha(source) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))
    validate_contract(reference)
    changed = candidates(originals)
    CHECKPOINT.mkdir(mode=0o700)
    evidence = {"kind": "astertv-v2-shared-header-rail-r16", "files": {}}
    for path, candidate in changed.items():
        relative = str(path.relative_to(ROOT))
        saved = CHECKPOINT / relative.replace("/", "__")
        saved.write_bytes(originals[path])
        saved.chmod(0o600)
        evidence["files"][relative] = {"before": sha(originals[path]), "after": sha(candidate)}
    (CHECKPOINT / "manifest.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, candidate in changed.items():
            atomic_write(path, candidate)
        for path, candidate in changed.items():
            if sha(path.read_bytes()) != sha(candidate):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, original in originals.items():
            atomic_write(path, original)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "files": {str(path.relative_to(ROOT)): sha(data)
                                for path, data in changed.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
