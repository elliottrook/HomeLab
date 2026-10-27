import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from release_inventory import InventoryError, build


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class ReleaseInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.family = b'{"kind":"family","schema":1}\n'
        self.recovery = json.dumps({"kind": "recovery", "schema": 1,
                                    "family_sha256": digest(self.family)},
                                   sort_keys=True).encode() + b"\n"
        for name, raw in (("family.json", self.family),
                          ("recovery.json", self.recovery)):
            path = self.root / "fixed" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.spec = {
            "schema": 1, "kind": "aster-release-inventory-spec.v1",
            "candidate": "test",
            "components": [
                {"name": "family", "path": "/fixed/family.json",
                 "sha256": digest(self.family), "kind": "family", "schema": 1},
                {"name": "recovery", "path": "/fixed/recovery.json",
                 "sha256": digest(self.recovery), "kind": "recovery", "schema": 1},
            ],
            "relations": [{"name": "recovery-covers-family",
                           "source": "recovery", "field": "family_sha256",
                           "target": "family", "required": False,
                           "recovery": True}],
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_verified_inventory_contains_hashes_not_contents(self):
        result = build(self.spec, self.root)
        self.assertTrue(result["complete"])
        self.assertTrue(result["recovery_complete"])
        self.assertEqual(result["relations"][0]["status"], "matched")
        rendered = json.dumps(result)
        self.assertNotIn("family_sha256", rendered)
        self.assertNotIn("cached media", result["components"])

    def test_optional_stale_recovery_is_truthfully_partial_not_failure(self):
        changed = json.loads(self.recovery)
        changed["family_sha256"] = "0" * 64
        raw = json.dumps(changed, sort_keys=True).encode() + b"\n"
        (self.root / "fixed/recovery.json").write_bytes(raw)
        self.spec["components"][1]["sha256"] = digest(raw)
        result = build(self.spec, self.root)
        self.assertTrue(result["complete"])
        self.assertFalse(result["recovery_complete"])
        self.assertEqual(result["relations"][0]["status"], "stale")

    def test_required_relation_fails_candidate_completeness(self):
        self.spec["relations"][0]["required"] = True
        self.spec["relations"][0]["field"] = "missing"
        self.assertFalse(build(self.spec, self.root)["complete"])

    def test_missing_required_and_digest_drift_fail_closed(self):
        (self.root / "fixed/family.json").unlink()
        with self.assertRaisesRegex(InventoryError, "required-anchor-missing"):
            build(self.spec, self.root)
        (self.root / "fixed/family.json").write_bytes(self.family + b" ")
        with self.assertRaisesRegex(InventoryError, "anchor-drift"):
            build(self.spec, self.root)

    def test_missing_optional_is_reported_without_read(self):
        self.spec["components"].append({
            "name": "optional", "path": "/fixed/optional.json",
            "sha256": "0" * 64, "required": False,
        })
        result = build(self.spec, self.root)
        self.assertEqual(result["components"][-1]["status"], "missing")

    def test_links_oversize_malformed_and_nonobjects_are_refused(self):
        path = self.root / "fixed/family.json"
        path.unlink(); path.symlink_to(self.root / "fixed/recovery.json")
        with self.assertRaisesRegex(InventoryError, "not-regular"):
            build(self.spec, self.root)
        path.unlink(); raw = b"x" * (1024 * 1024 + 1); path.write_bytes(raw)
        self.spec["components"][0]["sha256"] = digest(raw)
        with self.assertRaisesRegex(InventoryError, "anchor-size"):
            build(self.spec, self.root)
        for raw, error in ((b"not-json", "anchor-json"), (b"[]", "anchor-object")):
            path.write_bytes(raw); self.spec["components"][0]["sha256"] = digest(raw)
            with self.assertRaisesRegex(InventoryError, error):
                build(self.spec, self.root)

    def test_denied_paths_and_duplicate_names_are_refused(self):
        self.spec["components"][0]["path"] = "/storage/userdata/settings.json"
        with self.assertRaisesRegex(InventoryError, "anchor-denied"):
            build(self.spec, self.root)
        self.spec["components"][0]["path"] = "/fixed/family.json"
        self.spec["components"][1]["name"] = "family"
        with self.assertRaisesRegex(InventoryError, "component-duplicate"):
            build(self.spec, self.root)

    def test_opaque_anchor_is_hashed_without_parsing_or_content_output(self):
        raw = b"<addon password='never-export-this'/>"
        path = self.root / "fixed/addon.xml"; path.write_bytes(raw)
        self.spec["components"].append({
            "name": "addon-identity", "path": "/fixed/addon.xml",
            "sha256": digest(raw), "format": "opaque",
        })
        result = build(self.spec, self.root)
        self.assertEqual(result["components"][-1]["format"], "opaque")
        self.assertNotIn("never-export-this", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
