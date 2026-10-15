import unittest

from backup_receipt_adapter import (BackupReceiptError, verify_lxc110_mirror,
                                    verify_mac_pull_receipt, verify_mac_subset_receipt,
                                    verify_proxmox_artifacts)


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

    def subset_receipt(self):
        return {
            "path": "/mnt/Recovery/configuration/mac/",
            "claim": "source-destination-exact-subset", "date": "2026_10_13", "task_id": 2,
            "task_started_epoch": 1791971990, "task_finished_epoch": 1791972002,
            "source_snapshot_epoch": 1791971980, "destination_snapshot_epoch": 1791972005,
            "captured_epoch": 1791972010, "subset_manifest_sha256": "b" * 64,
            "source_manifest_sha256": "c" * 64, "destination_manifest_sha256": "c" * 64,
            "source_entry_count": 9, "destination_entry_count": 9,
            "source_total_size": 57692, "destination_total_size": 57692,
            "scan_consistent": True,
        }

    def test_mac_subset_receipt_proves_current_cycle_equality(self):
        self.assertEqual(
            verify_mac_subset_receipt(self.subset_receipt(), expected_manifest_sha256="b" * 64,
                                      date_prefix="2026_10_13", task_started_epoch=1791971990,
                                      task_finished_epoch=1791972002, lease_issued_epoch=1791972020),
            "mac-source-destination-subset-sha256:" + "b" * 64)

    def test_mac_subset_rejects_tree_presence_claim(self):
        receipt = self.subset_receipt()
        receipt["claim"] = "tree-present-only"
        with self.assertRaisesRegex(BackupReceiptError, "source/destination equality"):
            verify_mac_subset_receipt(receipt, expected_manifest_sha256="b" * 64,
                                      date_prefix="2026_10_13", task_started_epoch=1791971990,
                                      task_finished_epoch=1791972002, lease_issued_epoch=1791972020)


if __name__ == "__main__":
    unittest.main()
