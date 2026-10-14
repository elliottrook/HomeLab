"""Read-only backup-chain receipt parsing for the lease admission candidate.

The adapter accepts already captured fixed-source JSON. It does not execute
commands, alter schedules, or imply that a receipt is trustworthy unless both
the Proxmox artifact and fixed TrueNAS mirror metadata agree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


EXPECTED_GUESTS = ("104", "110", "116")
EXPECTED_PROXMOX_BACKUP_ID = "backup-49999802-1365"
EXPECTED_MIRROR_ROOT = "/mnt/Recovery/guests/aster-lxc110/"
EXPECTED_MAC_ROOT = "/mnt/Recovery/configuration/mac/"


class BackupReceiptError(ValueError):
    """The fixed backup sources do not provide a complete receipt."""


@dataclass(frozen=True)
class ArtifactReceipt:
    vmid: str
    volid: str
    size: int
    ctime: int


def _latest_artifacts(items: Iterable[dict[str, Any]], date_prefix: str) -> dict[str, ArtifactReceipt]:
    result: dict[str, ArtifactReceipt] = {}
    for item in items:
        vmid = str(item.get("vmid", ""))
        volid = item.get("volid", "")
        if vmid not in EXPECTED_GUESTS or date_prefix not in volid:
            continue
        if item.get("content") != "backup" or item.get("format") != "tar.zst":
            continue
        size = item.get("size")
        ctime = item.get("ctime")
        if not isinstance(size, int) or size <= 0 or not isinstance(ctime, int):
            raise BackupReceiptError("backup artifact metadata is incomplete")
        candidate = ArtifactReceipt(vmid, volid, size, ctime)
        previous = result.get(vmid)
        if previous is None or candidate.ctime > previous.ctime:
            result[vmid] = candidate
    if tuple(sorted(result)) != EXPECTED_GUESTS:
        raise BackupReceiptError("expected Proxmox guest artifacts are incomplete")
    return result


def verify_proxmox_artifacts(items: list[dict[str, Any]], *, date_prefix: str) -> tuple[ArtifactReceipt, ...]:
    """Verify fixed guest artifact metadata and return it in guest order."""
    latest = _latest_artifacts(items, date_prefix)
    return tuple(latest[vmid] for vmid in EXPECTED_GUESTS)


def verify_lxc110_mirror(items: list[dict[str, Any]], artifact: ArtifactReceipt) -> None:
    """Verify the fixed TrueNAS mirror has the exact LXC110 artifact metadata."""
    expected_name = artifact.volid.rsplit("/", 1)[-1]
    matches = [item for item in items if item.get("name") == expected_name]
    if len(matches) != 1:
        raise BackupReceiptError("expected LXC110 mirror artifact is absent or ambiguous")
    item = matches[0]
    if item.get("type") != "FILE" or item.get("path") != EXPECTED_MIRROR_ROOT + expected_name:
        raise BackupReceiptError("LXC110 mirror path or type is not fixed")
    if item.get("size") != artifact.size:
        raise BackupReceiptError("LXC110 mirror size differs from Proxmox artifact")


def verify_mac_pull_receipt(receipt: dict[str, Any], *, date_prefix: str, lease_issued_epoch: int) -> str:
    """Verify a content-free fixed-path summary of the Mac pull.

    The TrueNAS wrapper must aggregate the tree locally and return only this
    summary; filenames and file contents must never cross the observer
    boundary.  The digest is supplied by the wrapper over the fixed tree and
    is treated as candidate evidence until a trusted producer exists.
    """
    if receipt.get("path") != EXPECTED_MAC_ROOT:
        raise BackupReceiptError("Mac pull root is not fixed")
    if receipt.get("date") != date_prefix:
        raise BackupReceiptError("Mac pull receipt is from a different date")
    entry_count = receipt.get("entry_count")
    total_size = receipt.get("total_size")
    captured_epoch = receipt.get("captured_epoch")
    digest = receipt.get("tree_sha256")
    if not isinstance(entry_count, int) or entry_count <= 0:
        raise BackupReceiptError("Mac pull receipt is empty")
    if not isinstance(total_size, int) or total_size <= 0:
        raise BackupReceiptError("Mac pull receipt has no content size")
    if not isinstance(captured_epoch, int) or captured_epoch <= 0 or captured_epoch > lease_issued_epoch:
        raise BackupReceiptError("Mac pull receipt is not bound to the observed cycle")
    if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise BackupReceiptError("Mac pull receipt digest is invalid")
    return f"mac-tree-sha256:{digest}"
