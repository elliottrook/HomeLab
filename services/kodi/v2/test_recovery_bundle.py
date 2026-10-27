import hashlib
import tempfile
import unittest
from pathlib import Path

from recovery_bundle import audit, build, members, verify
from release_inventory import InventoryError


class RecoveryBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.stage = self.root / "storage/.aster-staging/layer"
        self.stage.mkdir(parents=True)
        (self.stage / "manifest.json").write_text('{"kind":"safe"}\n')
        (self.stage / "payload").mkdir(); (self.stage / "payload/code.py").write_text("pass\n")
        (self.stage / "result-1.json").write_text('{"private":"ignored"}')
        (self.stage / "deploy.lock").write_text("ignored")
        (self.stage / "._manifest.json").write_text("ignored")
        (self.stage / "data").symlink_to("/mnt/private-publications")
        _, _, digest = members(self.root, Path("/storage/.aster-staging/layer"))
        self.plan = {"sources": [{"path": "/storage/.aster-staging/layer",
                                   "tree_sha256": digest}]}

    def tearDown(self): self.temp.cleanup()

    def test_audit_and_deterministic_copy_exclude_transients(self):
        rows = audit(self.plan, self.root)
        self.assertEqual(rows[0]["files"], 2)
        out = self.root / "bundle"; pin = build(self.plan, self.root, out)
        self.assertEqual(len(pin), 64)
        self.assertEqual(verify(out, pin)["files"], 2)
        self.assertTrue((out / "sources/layer/payload/code.py").is_file())
        self.assertFalse((out / "sources/layer/result-1.json").exists())

    def test_drift_link_private_member_and_existing_output_fail_closed(self):
        self.plan["sources"][0]["tree_sha256"] = "0" * 64
        with self.assertRaisesRegex(InventoryError, "source-drift"):
            audit(self.plan, self.root)
        _, _, digest = members(self.root, Path("/storage/.aster-staging/layer"))
        self.plan["sources"][0]["tree_sha256"] = digest
        (self.stage / "linked").symlink_to(self.stage / "manifest.json")
        with self.assertRaisesRegex(InventoryError, "linked-member"):
            audit(self.plan, self.root)
        (self.stage / "linked").unlink(); (self.stage / "api_keys.json").write_text("secret")
        with self.assertRaisesRegex(InventoryError, "private-member"):
            audit(self.plan, self.root)
        (self.stage / "api_keys.json").unlink(); out = self.root / "exists"; out.mkdir()
        with self.assertRaisesRegex(InventoryError, "output-exists"):
            build(self.plan, self.root, out)

    def test_verify_refuses_drift_and_extra_files(self):
        out = self.root / "bundle"; pin = build(self.plan, self.root, out)
        target = out / "sources/layer/payload/code.py"
        target.write_text("changed\n")
        with self.assertRaisesRegex(InventoryError, "verify-drift"):
            verify(out, pin)
        target.write_text("pass\n"); (out / "extra").write_text("unexpected")
        with self.assertRaisesRegex(InventoryError, "verify-extra"):
            verify(out, pin)


if __name__ == "__main__": unittest.main()
