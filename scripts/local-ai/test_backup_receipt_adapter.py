import unittest

from backup_receipt_adapter import BackupReceiptError, verify_lxc110_mirror, verify_proxmox_artifacts


class BackupReceiptAdapterTests(unittest.TestCase):
    def artifacts(self):
        return [
            {"content": "backup", "format": "tar.zst", "vmid": vmid, "ctime": 100 + int(vmid), "size": 1000 + int(vmid), "volid": f"backups:backup/vzdump-lxc-{vmid}-2026_10_13-00_40_00.tar.zst"}
            for vmid in ("104", "110", "116")
        ]

    def test_requires_all_expected_guest_artifacts(self):
        result = verify_proxmox_artifacts(self.artifacts(), date_prefix="2026_10_13")
        self.assertEqual(tuple(item.vmid for item in result), ("104", "110", "116"))
        with self.assertRaisesRegex(BackupReceiptError, "incomplete"):
            verify_proxmox_artifacts(self.artifacts()[:2], date_prefix="2026_10_13")

    def test_requires_exact_lxc110_mirror_metadata(self):
        artifact = verify_proxmox_artifacts(self.artifacts(), date_prefix="2026_10_13")[1]
        name = artifact.volid.rsplit("/", 1)[-1]
        verify_lxc110_mirror([{"name": name, "path": f"/mnt/Recovery/guests/aster-lxc110/{name}", "type": "FILE", "size": artifact.size}], artifact)
        with self.assertRaisesRegex(BackupReceiptError, "size"):
            verify_lxc110_mirror([{"name": name, "path": f"/mnt/Recovery/guests/aster-lxc110/{name}", "type": "FILE", "size": 1}], artifact)


if __name__ == "__main__":
    unittest.main()
