import copy
import hashlib
import json
import unittest

from evaluation_lease import (
    D4_DIGEST as LEASE_D4_DIGEST,
    M3_STAGE_MANIFEST_DIGEST as LEASE_M3_STAGE_MANIFEST_DIGEST,
)
from stream_a_evaluation_outcome_verifier import (
    D4_DIGEST, M3_CANDIDATE_SHA256, M3_ENGINE_SHA256, M3_JOURNAL_SCHEMA,
    M3_POLICY_SHA256, M3_RELEASE_SHA256, M3_RUN_SCHEMA,
    M3_STAGE_MANIFEST_DIGEST,
    OutcomeVerificationError, verify_d4_ledger, verify_m3_artifacts,
)


def digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def d4_ledger():
    rows = []; previous = ""
    for index in range(12):
        case_id = f"sa3-dev-{index + 1:02d}"
        for event in (
            {"type": "started", "case_id": case_id, "mode": "nonthinking"},
            {"type": "finished", "result": {
                "case_id": case_id, "mode": "nonthinking", "status": "conclude",
                "steps": [{"metadata": {}, "answer": {}}], "attempted_calls": 1,
                "elapsed_seconds": 1.5, "failure": None,
                "limit": "synthetic development only; terminal status is not a correctness grade",
            }},
        ):
            row = {"release": D4_DIGEST, "previous": previous, "event": event}
            row["digest"] = digest(row); previous = row["digest"]; rows.append(row)
    return ("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n").encode()


def interpretation(case_id):
    return {
        "schema_version": "request-interpretation.v1", "request_id": case_id,
        "principal_ref": "nlu-calibration-v1", "request_family": "general-answer",
        "sensitivity": "internal", "capability_needs": [], "ambiguity": "ambiguous",
        "disposition": "clarify", "reason": "ambiguous",
        "engine_digest": "sha256:" + M3_ENGINE_SHA256,
        "policy_digest": "sha256:" + M3_POLICY_SHA256,
        "confidence": None, "authorization": "not-granted",
    }


def m3_artifacts():
    records = [{"id": f"case-{index:02d}", "valid": True,
                "latency_seconds": 1.0,
                "interpretation": interpretation(f"case-{index:02d}")}
               for index in range(60)]
    run = {
        "schema": M3_RUN_SCHEMA, "candidate_bundle_sha256": M3_CANDIDATE_SHA256,
        "calibration_artifact_sha256": M3_RELEASE_SHA256,
        "engine_sha256": M3_ENGINE_SHA256, "policy_sha256": M3_POLICY_SHA256,
        "records": records, "authority": "not-granted",
    }
    rows = [{"event": "run_started", "schema": M3_JOURNAL_SCHEMA,
             "candidate_bundle_sha256": M3_CANDIDATE_SHA256,
             "calibration_artifact_sha256": M3_RELEASE_SHA256,
             "planned": 60, "authority": "not-granted"}]
    for record in records:
        rows.extend((
            {"event": "attempt_started", "case_id": record["id"]},
            {"event": "attempt_recorded", "case_id": record["id"],
             "valid": True},
        ))
    rows.append({"event": "run_finished", "attempted": 60, "complete": True})
    raw_run = (json.dumps(run, sort_keys=True, separators=(",", ":")) + "\n").encode()
    raw_journal = ("\n".join(json.dumps(row, sort_keys=True,
                                         separators=(",", ":")) for row in rows) + "\n").encode()
    return raw_run, raw_journal


class OutcomeVerifierTests(unittest.TestCase):
    def test_guest_release_identities_match_host_lease_contract(self):
        self.assertEqual(D4_DIGEST, LEASE_D4_DIGEST)
        self.assertEqual(M3_STAGE_MANIFEST_DIGEST,
                         LEASE_M3_STAGE_MANIFEST_DIGEST)

    def test_accepts_exact_d4_chain_and_returns_content_free_evidence(self):
        raw = d4_ledger(); result = verify_d4_ledger(raw)
        self.assertEqual(result.calls, 12)
        self.assertEqual(result.journal_digest, hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(result.result_digest), 64)

    def test_d4_rejects_chain_drift_and_nonterminal_result(self):
        raw = d4_ledger().replace(D4_DIGEST.encode(), b"0" * 64, 1)
        with self.assertRaises(OutcomeVerificationError): verify_d4_ledger(raw)
        rows = [json.loads(line) for line in d4_ledger().splitlines()]
        rows[1]["event"]["result"]["status"] = "time_budget_exhausted"
        raw = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
        with self.assertRaises(OutcomeVerificationError): verify_d4_ledger(raw)

    def test_d4_rejects_arbitrary_unique_case_set(self):
        rows = [json.loads(line) for line in d4_ledger().splitlines()]
        previous = ""
        for index, row in enumerate(rows):
            if index == 0:
                row["event"]["case_id"] = "arbitrary-unique"
            elif index == 1:
                row["event"]["result"]["case_id"] = "arbitrary-unique"
            row["previous"] = previous
            sealed = dict(row); sealed.pop("digest", None)
            row["digest"] = digest(sealed); previous = row["digest"]
        raw = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
        with self.assertRaisesRegex(OutcomeVerificationError, "incomplete"):
            verify_d4_ledger(raw)

    def test_accepts_exact_m3_run_and_journal(self):
        run, journal = m3_artifacts(); result = verify_m3_artifacts(run, journal)
        self.assertEqual(result.calls, 60)
        self.assertEqual(result.journal_digest, hashlib.sha256(journal).hexdigest())

    def test_m3_rejects_duplicate_case_and_journal_drift(self):
        run_raw, journal = m3_artifacts(); run = json.loads(run_raw)
        run["records"][1]["id"] = run["records"][0]["id"]
        run["records"][1]["interpretation"]["request_id"] = run["records"][0]["id"]
        with self.assertRaises(OutcomeVerificationError):
            verify_m3_artifacts((json.dumps(run) + "\n").encode(), journal)
        with self.assertRaises(OutcomeVerificationError):
            verify_m3_artifacts(run_raw, journal.replace(b'"complete":true', b'"complete":false'))

    def test_m3_rejects_malformed_interpretation_dimensions(self):
        run_raw, journal = m3_artifacts(); run = json.loads(run_raw)
        for field, value in (
            ("request_family", "invented"), ("sensitivity", 7),
            ("capability_needs", ["root.anything"]),
            ("ambiguity", []), ("disposition", "route"),
            ("reason", "unsupported"),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(run)
                changed["records"][0]["interpretation"][field] = value
                with self.assertRaises(OutcomeVerificationError):
                    verify_m3_artifacts((json.dumps(changed) + "\n").encode(), journal)

    def test_duplicate_json_and_oversize_fail_closed(self):
        _run, journal = m3_artifacts()
        duplicate = b'{"schema":"x","schema":"x"}\n'
        with self.assertRaises(OutcomeVerificationError):
            verify_m3_artifacts(duplicate, journal)
        with self.assertRaisesRegex(OutcomeVerificationError, "size"):
            verify_d4_ledger(b"x" * (4 * 1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
