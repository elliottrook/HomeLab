import copy
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import sa4_inactive_install_packet_v1 as packet


class SA4InactiveInstallPacketTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parents[2]
        self.absent = {path for path, _, _, _ in packet.DIRECTORIES}
        self.absent.update(item.destination for item in packet.PAYLOADS)

    def test_every_payload_is_hash_pinned_to_source(self):
        for item in packet.PAYLOADS:
            with self.subTest(source=item.source):
                self.assertEqual(item.sha256, hashlib.sha256(
                    (self.root / item.source).read_bytes()).hexdigest())

    def test_plan_is_inert_exact_and_reversible(self):
        value = packet.plan(observed_absent_paths=self.absent)
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["key_slots_populated"])
        self.assertEqual("off", value["automatic_routing"])
        installed = [item["destination"] for item in value["payloads"]]
        self.assertEqual(list(reversed(installed)),
                         value["rollback"]["remove_files"])
        self.assertEqual("retain-and-stop",
                         value["rollback"]["on_uncertainty"])
        self.assertIn("no-service-unit-timer-or-booking", value["exclusions"])
        self.assertIn("no-overwrite-of-existing-path", value["exclusions"])

    def test_installed_program_set_has_closed_imports_in_isolation(self):
        programs = [item for item in packet.PAYLOADS
                    if item.destination.startswith(packet.LIBEXEC + "/")]
        with tempfile.TemporaryDirectory() as raw:
            isolated = Path(raw)
            for item in programs:
                shutil.copyfile(self.root / item.source,
                                isolated / Path(item.destination).name)
            modules = sorted(Path(item.destination).stem for item in programs)
            statement = ("import sys; sys.path.insert(0, %r); " % raw
                         + "; ".join("import " + name for name in modules))
            result = subprocess.run(
                [sys.executable, "-I", "-B", "-c", statement],
                cwd=raw, check=False, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_any_missing_or_extra_absence_observation_fails_closed(self):
        missing = set(self.absent); missing.remove(packet.TARGET)
        extra = set(self.absent); extra.add("/tmp/not-part-of-packet")
        for observed in (missing, extra, set()):
            with self.subTest(size=len(observed)), self.assertRaises(ValueError):
                packet.plan(observed_absent_paths=observed)

    def test_packet_rejects_mutated_payload_or_directory(self):
        original_payloads = packet.PAYLOADS
        original_directories = packet.DIRECTORIES
        try:
            changed = list(packet.PAYLOADS)
            changed[0] = copy.copy(changed[0]).__class__(
                changed[0].source, "/etc/aster/unsafe.py", changed[0].sha256)
            packet.PAYLOADS = tuple(changed)
            with self.assertRaises(ValueError):
                packet.validate_packet()
            packet.PAYLOADS = original_payloads
            packet.DIRECTORIES = original_directories + (("/tmp/extra", "root", "root", "0755"),)
            with self.assertRaises(ValueError):
                packet.validate_packet()
        finally:
            packet.PAYLOADS = original_payloads
            packet.DIRECTORIES = original_directories


if __name__ == "__main__":
    unittest.main()
