import unittest

from backup_receipt_adapter import BackupReceiptError, verify_lxc110_mirror, verify_mac_pull_receipt, verify_proxmox_artifacts


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

    def mac_receipt(self):
        return {"path": "/mnt/Recovery/configuration/mac/", "claim": "tree-present-only", "date": "2026_10_13", "entry_count": 12, "total_size": 4096, "captured_epoch": 1791972010, "task_finished_epoch": 1791972002, "scan_elapsed_ms": 10, "scan_consistent": True, "tree_sha256": "a" * 64}

    def test_requires_content_free_mac_pull_summary(self):
        self.assertEqual(verify_mac_pull_receipt(self.mac_receipt(), date_prefix="2026_10_13", task_finished_epoch=1791972002, lease_issued_epoch=1791972020), "mac-tree-present-sha256:" + "a" * 64)

    def test_rejects_mac_summary_scope_date_empty_or_stale(self):
        receipt = self.mac_receipt()
        for key, value, message in (("path", "/mnt/Recovery/configuration/other/", "root"), ("date", "2026_10_12", "different"), ("entry_count", 0, "empty"), ("captured_epoch", 1791972030, "stale")):
            candidate = dict(receipt)
            candidate[key] = value
            with self.assertRaisesRegex(BackupReceiptError, message):
                verify_mac_pull_receipt(candidate, date_prefix="2026_10_13", task_finished_epoch=1791972002, lease_issued_epoch=1791972020)

    def test_rejects_mac_summary_with_invalid_digest(self):
        receipt = self.mac_receipt()
        receipt["tree_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(BackupReceiptError, "digest"):
            verify_mac_pull_receipt(receipt, date_prefix="2026_10_13", task_finished_epoch=1791972002, lease_issued_epoch=1791972020)


if __name__ == "__main__":
    unittest.main()
