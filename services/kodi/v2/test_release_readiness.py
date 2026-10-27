import unittest

from release_readiness import ReadinessError, build


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "schema": 1,
            "kind": "aster-release-readiness-spec.v1",
            "candidate": "test",
            "gates": [
                {"id": "automated", "category": "automated",
                 "status": "passed", "evidence": ["tests pass"]},
                {"id": "owner", "category": "owner",
                 "status": "input-required", "blockers": ["owner review"]},
                {"id": "promotion", "category": "promotion",
                 "status": "approval-required", "blockers": ["not approved"]},
            ],
        }

    def test_open_human_gates_do_not_erase_engineering_success(self):
        result = build(self.spec)
        self.assertTrue(result["engineering_checks_passed"])
        self.assertFalse(result["release_ready"])
        self.assertFalse(result["production_authorized"])
        self.assertEqual(result["counts"]["passed"], 1)

    def test_all_passed_is_release_ready_and_authorized(self):
        for gate in self.spec["gates"]:
            gate["status"] = "passed"
            gate["evidence"] = ["verified"]
            gate["blockers"] = []
        result = build(self.spec)
        self.assertTrue(result["release_ready"])
        self.assertTrue(result["production_authorized"])

    def test_passed_gate_requires_evidence_and_no_blocker(self):
        self.spec["gates"][0]["evidence"] = []
        with self.assertRaisesRegex(ReadinessError, "passed-evidence"):
            build(self.spec)
        self.spec["gates"][0]["evidence"] = ["ok"]
        self.spec["gates"][0]["blockers"] = ["contradiction"]
        with self.assertRaisesRegex(ReadinessError, "passed-evidence"):
            build(self.spec)

    def test_open_gate_requires_explicit_blocker(self):
        self.spec["gates"][1]["blockers"] = []
        with self.assertRaisesRegex(ReadinessError, "open-blocker"):
            build(self.spec)

    def test_destructive_gate_cannot_be_silently_passed(self):
        self.spec["gates"].insert(1, {
            "id": "clean-install", "category": "destructive",
            "status": "passed", "destructive": True,
            "evidence": ["claimed"],
        })
        with self.assertRaisesRegex(ReadinessError, "destructive-boundary"):
            build(self.spec)

    def test_duplicate_unknown_and_missing_promotion_are_refused(self):
        self.spec["gates"][1]["id"] = "automated"
        with self.assertRaisesRegex(ReadinessError, "duplicate"):
            build(self.spec)
        self.spec["gates"][1]["id"] = "owner"
        self.spec["gates"][1]["status"] = "maybe"
        with self.assertRaisesRegex(ReadinessError, "status"):
            build(self.spec)
        self.spec["gates"][1]["status"] = "input-required"
        self.spec["gates"] = self.spec["gates"][:-1]
        with self.assertRaisesRegex(ReadinessError, "promotion-gate"):
            build(self.spec)


if __name__ == "__main__":
    unittest.main()
