import hashlib
import json
import unittest

from diagnostic_catalogue_v3 import CatalogueError, build_catalogue, select_check


RUN = "a" * 32
AGGREGATE = b'{"schema":1,"status":"failed"}\n'
ALLOWED = {"aster.agent_inference", "backup.proxmox_current_cycle"}


def event(check_id, state, run_id=RUN):
    return json.dumps({"run_id": run_id, "check_id": check_id, "state": state}).encode() + b"\n"


class DiagnosticCatalogueV3Tests(unittest.TestCase):
    def build(self, raw=b"", status="failed"):
        return build_catalogue(
            raw,
            run_id=RUN,
            generated_at="2026-10-26T20:00:00+00:00",
            aggregate_payload=AGGREGATE,
            aggregate_status=status,
            allowed_check_ids=ALLOWED,
        )

    def test_multiple_named_checks_are_sorted_and_digest_bound(self):
        value = self.build(event("backup.proxmox_current_cycle", "warn") + event("aster.agent_inference", "fail"))
        self.assertEqual(3, value["schema"])
        self.assertEqual(hashlib.sha256(AGGREGATE).hexdigest(), value["source_report_digest"])
        self.assertEqual([
            {"check_id": "aster.agent_inference", "state": "fail"},
            {"check_id": "backup.proxmox_current_cycle", "state": "warn"},
        ], value["checks"])

    def test_missing_allowlisted_event_is_unavailable(self):
        value = self.build(event("aster.agent_inference", "pass"))
        self.assertEqual("unavailable", value["checks"][1]["state"])

    def test_unknown_duplicate_cross_run_and_extra_fields_reject_all(self):
        cases = [
            event("unknown.check", "pass"),
            event("aster.agent_inference", "pass") * 2,
            event("aster.agent_inference", "pass", "b" * 32),
            b'{"run_id":"' + RUN.encode() + b'","check_id":"aster.agent_inference","state":"pass","summary":"private"}\n',
            b'{"run_id":"' + RUN.encode() + b'","check_id":"aster.agent_inference","state":"pass","state":"fail"}\n',
            b'{"run_id":"' + RUN.encode() + b'","check_id":"aster.agent_inference","state":[]}\n',
        ]
        for raw in cases:
            with self.subTest(raw=raw[:50]), self.assertRaises(CatalogueError):
                self.build(raw)

    def test_severity_cannot_exceed_aggregate(self):
        for raw, status in (
            (event("aster.agent_inference", "warn"), "healthy"),
            (event("aster.agent_inference", "fail"), "warning"),
        ):
            with self.subTest(status=status), self.assertRaises(CatalogueError):
                self.build(raw, status)

    def test_selector_exposes_only_one_fixed_check(self):
        catalogue = self.build(event("aster.agent_inference", "fail"))
        digest = hashlib.sha256(AGGREGATE).hexdigest()
        self.assertEqual(
            {"check_id": "aster.agent_inference", "state": "fail"},
            select_check(catalogue, check_id="aster.agent_inference", source_report_digest=digest),
        )
        with self.assertRaises(CatalogueError):
            select_check(catalogue, check_id="not.allowlisted", source_report_digest=digest)

    def test_selector_rejects_duplicate_or_tampered_catalogue(self):
        digest = hashlib.sha256(AGGREGATE).hexdigest()
        duplicate = self.build(event("aster.agent_inference", "pass"))
        duplicate["checks"].append(dict(duplicate["checks"][0]))
        with self.assertRaises(CatalogueError):
            select_check(duplicate, check_id="aster.agent_inference", source_report_digest=digest)
        valid = self.build()
        with self.assertRaises(CatalogueError):
            select_check(valid, check_id="aster.agent_inference", source_report_digest="0" * 64)


if __name__ == "__main__":
    unittest.main()
