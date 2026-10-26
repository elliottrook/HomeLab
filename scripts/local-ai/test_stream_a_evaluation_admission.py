import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from stream_a_evaluation_admission import (
    ADMISSION_PREFIX, ADMISSION_SCHEMA, EXPECTED_BACKEND,
    EXPECTED_D4_DIGEST, EXPECTED_M3_DIGEST, EXPECTED_MODEL, F2_PREFIX,
    F3_PREFIX, F5_SCHEMA, AdmissionArtifactError, canonical_bytes,
    build_admission, load_bound_admission, validate_admission, validate_f5,
)


class AdmissionArtifactTests(unittest.TestCase):
    def f5(self):
        return {
            "schema": F5_SCHEMA, "cycle_date": "2026-10-26",
            "observed_epoch": 1000, "expires_epoch": 1800,
            "f2_result_sha256": "b" * 64, "f3_receipt_sha256": "c" * 64,
            "f4_receipt_sha256": "d" * 64,
            "lxc110_mirror_identity": "task2:2026-10-26T02:00:00-07:00:success",
            "schedule_set_sha256": "e" * 64, "model": EXPECTED_MODEL,
            "binary_sha256": "f" * 64, "unit_sha256": "1" * 64,
            "auth_identity": "aster-llama-key-file-v1",
            "consumer_baseline_sha256": "2" * 64,
            "conflicting_lease": False, "conflicting_job": False,
        }

    def admission(self, f5_digest):
        return {
            "schema": ADMISSION_SCHEMA, "cycle_date": "2026-10-26",
            "lease_id": "eval-20261026-1", "generation": 1,
            "created_epoch": 1000, "expires_epoch": 1800,
            "backup_receipt": "retained-archive-integrity-sha256:" + "a" * 64,
            "f2_result_sha256": "b" * 64, "f3_receipt_sha256": "c" * 64,
            "f4_receipt_sha256": "d" * 64,
            "f5_observation_sha256": f5_digest,
            "d4_run_digest": EXPECTED_D4_DIGEST,
            "m3_manifest_sha256": EXPECTED_M3_DIGEST,
            "model": EXPECTED_MODEL, "backend": EXPECTED_BACKEND,
        }

    def files(self):
        temporary = tempfile.TemporaryDirectory()
        parent = Path(temporary.name) / "stream-a-evaluation"
        parent.mkdir(mode=0o700)
        parent.chmod(0o700)
        f5_path = parent / "f5-observation.json"
        f5_raw = canonical_bytes(self.f5())
        f5_path.write_bytes(f5_raw); f5_path.chmod(0o600)
        admission = self.admission(hashlib.sha256(f5_raw).hexdigest())
        admission_path = parent / "admission.json"
        admission_raw = canonical_bytes(admission)
        admission_path.write_bytes(admission_raw); admission_path.chmod(0o600)
        return temporary, admission_path, f5_path, admission, admission_raw

    def load(self, admission_path, f5_path, raw, **changes):
        values = {
            "receipt": ADMISSION_PREFIX + hashlib.sha256(raw).hexdigest(),
            "lease_id": "eval-20261026-1", "generation": 1,
            "backup_receipt": "retained-archive-integrity-sha256:" + "a" * 64,
            "f2_receipt": F2_PREFIX + "b" * 64,
            "f3_receipt": F3_PREFIX + "c" * 64,
            "now_epoch": 1100, "require_fresh": True,
            "required_uid": os.geteuid(),
        }
        values.update(changes)
        return load_bound_admission(admission_path, f5_path, **values)

    def test_exact_fresh_artifacts_bind_all_predecessors(self):
        temporary, admission_path, f5_path, _value, raw = self.files()
        with temporary:
            bound = self.load(admission_path, f5_path, raw)
            self.assertEqual(bound.receipt, ADMISSION_PREFIX + bound.digest)

    def test_builder_hashes_exact_predecessor_bytes(self):
        f2, f3, f4 = b"f2\n", b"f3\n", b"f4\n"
        f5 = self.f5()
        f5["f2_result_sha256"] = hashlib.sha256(f2).hexdigest()
        f5["f3_receipt_sha256"] = hashlib.sha256(f3).hexdigest()
        f5["f4_receipt_sha256"] = hashlib.sha256(f4).hexdigest()
        value = build_admission(
            cycle_date="2026-10-26", lease_id="eval-1", generation=1,
            created_epoch=1100, expires_epoch=1800,
            backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            f2_bytes=f2, f3_bytes=f3, f4_bytes=f4,
            f5_bytes=canonical_bytes(f5),
        )
        self.assertEqual(value["f2_result_sha256"], hashlib.sha256(f2).hexdigest())
        with self.assertRaises(AdmissionArtifactError):
            build_admission(
                cycle_date="2026-10-26", lease_id="eval-1", generation=1,
                created_epoch=1100, expires_epoch=1800,
                backup_receipt=value["backup_receipt"], f2_bytes=b"substitute\n",
                f3_bytes=f3, f4_bytes=f4, f5_bytes=canonical_bytes(f5),
            )

    def test_post_quiescence_reuses_bytes_without_reapplying_freshness(self):
        temporary, admission_path, f5_path, _value, raw = self.files()
        with temporary:
            self.load(admission_path, f5_path, raw, now_epoch=5000,
                      require_fresh=False)
            with self.assertRaises(AdmissionArtifactError):
                self.load(admission_path, f5_path, raw, now_epoch=5000,
                          require_fresh=True)

    def test_digest_lease_generation_and_predecessor_substitution_fail(self):
        temporary, admission_path, f5_path, _value, raw = self.files()
        with temporary:
            mutations = (
                {"receipt": ADMISSION_PREFIX + "9" * 64},
                {"lease_id": "foreign"}, {"generation": 2},
                {"f2_receipt": F2_PREFIX + "9" * 64},
                {"f3_receipt": F3_PREFIX + "9" * 64},
                {"backup_receipt": "retained-archive-integrity-sha256:" + "9" * 64},
            )
            for mutation in mutations:
                with self.subTest(mutation=mutation), self.assertRaises(AdmissionArtifactError):
                    self.load(admission_path, f5_path, raw, **mutation)

    def test_cross_cycle_and_f4_f5_substitution_fail(self):
        temporary, admission_path, f5_path, admission, _raw = self.files()
        with temporary:
            for field, value in (("cycle_date", "2026-10-25"),
                                 ("f4_receipt_sha256", "9" * 64)):
                f5 = self.f5(); f5[field] = value
                f5_path.write_bytes(canonical_bytes(f5)); f5_path.chmod(0o600)
                admission["f5_observation_sha256"] = hashlib.sha256(f5_path.read_bytes()).hexdigest()
                raw = canonical_bytes(admission)
                admission_path.write_bytes(raw); admission_path.chmod(0o600)
                with self.subTest(field=field), self.assertRaises(AdmissionArtifactError):
                    self.load(admission_path, f5_path, raw)

    def test_duplicate_keys_noncanonical_mode_and_link_fail_closed(self):
        temporary, admission_path, f5_path, _value, raw = self.files()
        with temporary:
            admission_path.write_text('{"schema":"x","schema":"y"}\n')
            admission_path.chmod(0o600)
            with self.assertRaises(AdmissionArtifactError):
                self.load(admission_path, f5_path, admission_path.read_bytes())
            admission_path.write_bytes(raw); admission_path.chmod(0o644)
            with self.assertRaises(AdmissionArtifactError):
                self.load(admission_path, f5_path, raw)
            admission_path.chmod(0o600)
            alias = admission_path.parent / "alias.json"
            os.link(admission_path, alias)
            with self.assertRaises(AdmissionArtifactError):
                self.load(admission_path, f5_path, raw)

    def test_stale_future_and_overlong_windows_fail(self):
        f5 = self.f5()
        admission = self.admission("a" * 64)
        for created, expires, now in ((1000, 1100, 1200), (1200, 1300, 1100),
                                      (1000, 2000, 1100)):
            admission["created_epoch"], admission["expires_epoch"] = created, expires
            with self.subTest(created=created), self.assertRaises(AdmissionArtifactError):
                validate_admission(admission, now_epoch=now)
            f5["observed_epoch"], f5["expires_epoch"] = created, expires
            with self.assertRaises(AdmissionArtifactError):
                validate_f5(f5, now_epoch=now)

    def test_model_backend_and_workload_drift_fail(self):
        admission = self.admission("a" * 64)
        for field in ("model", "backend", "d4_run_digest", "m3_manifest_sha256"):
            changed = dict(admission); changed[field] = "9" * 64
            with self.subTest(field=field), self.assertRaises(AdmissionArtifactError):
                validate_admission(changed, now_epoch=1100)


if __name__ == "__main__":
    unittest.main()
