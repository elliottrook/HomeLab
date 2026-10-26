import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.deploy import patch_live_doctor_structured_emitter as subject


FIXTURE = '''#!/bin/bash
source "$REPO/scripts/lib/output.sh"
check_aster() {
    if ! state="$(
        fixture
    )"; then
        warn "Unable to check Aster services"
        return
    fi
    if healthy; then
        pass "Aster agent API, B60 Vulkan and llama.cpp inference healthy"
    else
        fail "Aster service unhealthy: $state"
    fi
}

check_aster_lab_operations() {
    fixture
}
'''


class LiveDoctorEmitterPatchTest(unittest.TestCase):
    def test_adds_helper_and_replaces_only_aster_check_contract(self):
        result = subject.patch_text(FIXTURE)
        self.assertEqual(result.count("doctor_emit_aster_state()"), 1)
        self.assertEqual(result.count("doctor_emit_aster_state unavailable"), 1)
        self.assertEqual(result.count("doctor_emit_aster_state pass"), 1)
        self.assertEqual(result.count("doctor_emit_aster_state fail"), 1)
        self.assertNotIn("B60 Vulkan and llama.cpp inference healthy", result)
        self.assertIn("B60 xe bound; GPU offload not verified", result)
        self.assertIn("check_aster_lab_operations()", result)

    def test_rejects_missing_or_duplicate_anchor(self):
        with self.assertRaisesRegex(ValueError, "helper anchor count"):
            subject.patch_text(FIXTURE.replace('source "$REPO/scripts/lib/output.sh"\n', ''))
        with self.assertRaisesRegex(ValueError, "helper anchor count"):
            subject.patch_text(FIXTURE.replace(
                'source "$REPO/scripts/lib/output.sh"\n',
                'source "$REPO/scripts/lib/output.sh"\nsource "$REPO/scripts/lib/output.sh"\n',
            ))

    def test_builder_requires_exact_predecessor_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "doctor.sh"
            destination = Path(directory) / "candidate.sh"
            source.write_text(FIXTURE)
            with patch.object(subject, "CURRENT_SHA256", subject.sha256(source.read_bytes())), \
                 patch.object(subject, "EXPECTED_SHA256", "TO_BE_FROZEN"):
                observed = subject.build(source, destination)
                self.assertEqual(observed, subject.sha256(destination.read_bytes()))
                self.assertEqual(destination.stat().st_mode & 0o777, 0o700)
                with self.assertRaises(FileExistsError):
                    subject.build(source, destination)
            source.write_text(FIXTURE + "# drift\n")
            with self.assertRaisesRegex(ValueError, "predecessor hash mismatch"):
                subject.build(source, Path(directory) / "other.sh")


if __name__ == "__main__":
    unittest.main()
