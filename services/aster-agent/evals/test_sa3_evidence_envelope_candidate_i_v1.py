import copy
import json
import tempfile
import unittest
from pathlib import Path

import sa3_evidence_envelope_candidate_i_v1 as candidate


ROOT = Path(__file__).parent
MANIFEST = ROOT / "sa3-evidence-envelope-candidate-i-v1.json"


class EvidenceEnvelopeCandidateITests(unittest.TestCase):
    def test_exact_source_freeze(self):
        value = candidate.load(MANIFEST)
        self.assertTrue(value["source_frozen"])
        self.assertTrue(value["untouched_evaluation_required"])
        self.assertFalse(value["model_calls_authorized"])
        self.assertEqual("none", value["authority"])

    def test_authority_or_evaluation_weakening_fails(self):
        manifest = json.loads(MANIFEST.read_text())
        changes = (
            ("authority", "granted"),
            ("automatic_routing", "on"),
            ("model_calls_authorized", True),
            ("status", "released"),
        )
        for field, changed in changes:
            value = copy.deepcopy(manifest); value[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                candidate.validate(value, ROOT)
        value = copy.deepcopy(manifest)
        value["evaluation"]["required_passes"] = 17
        with self.assertRaises(ValueError): candidate.validate(value, ROOT)

    def test_spent_packet_hashes_are_explicitly_forbidden(self):
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(candidate.FORBIDDEN,
                         set(manifest["forbidden_evaluation_sha256"]))
        value = copy.deepcopy(manifest)
        value["forbidden_evaluation_sha256"].pop()
        with self.assertRaises(ValueError): candidate.validate(value, ROOT)

    def test_missing_changed_or_symlink_source_fails(self):
        manifest = json.loads(MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for name in candidate.FILES:
                (target / name).write_bytes((ROOT / name).read_bytes())
            (target / "sa3_deterministic_evidence_envelope_v2.py").write_text("changed")
            with self.assertRaises(ValueError): candidate.validate(manifest, target)
            (target / "sa3_deterministic_evidence_envelope_v2.py").unlink()
            (target / "sa3_deterministic_evidence_envelope_v2.py").symlink_to(
                ROOT / "sa3_deterministic_evidence_envelope_v2.py")
            with self.assertRaises(ValueError): candidate.validate(manifest, target)


if __name__ == "__main__": unittest.main()
