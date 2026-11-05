import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


MODULE_PATH = Path(__file__).with_name("correct_family_tcl_reservation_mac.py")
SPEC = importlib.util.spec_from_file_location("correct_family_tcl_reservation_mac", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CorrectFamilyTclReservationMacTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = root / "config.xml"
        self.checkpoint = root / "checkpoint.xml"
        self.proof = root / "proof.json"
        self.before = b"""<opnsense><dnsmasq>
<hosts uuid="bf6b7e34-99a2-4bce-928d-ed042a9fcf84">
<host>family-room-tv</host><ip>192.168.30.162</ip>
<hwaddr>0c:91:60:75:7c:5d</hwaddr>
</hosts></dnsmasq></opnsense>"""
        self.config.write_bytes(self.before)
        MODULE.CONFIG = self.config
        MODULE.CHECKPOINT = self.checkpoint
        MODULE.PROOF = self.proof
        MODULE.EXPECTED = hashlib.sha256(self.before).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def test_apply_and_exact_rollback(self):
        MODULE.apply()
        host = ET.parse(self.config).getroot().find("dnsmasq/hosts")
        self.assertEqual(host.findtext("hwaddr"), "0c:91:60:75:7c:5c")
        MODULE.rollback()
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_wrong_old_mac_fails_closed(self):
        tree = ET.parse(self.config)
        tree.getroot().find("dnsmasq/hosts/hwaddr").text = "00:00:00:00:00:00"
        tree.write(self.config, encoding="utf-8")
        MODULE.EXPECTED = hashlib.sha256(self.config.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError, "reservation-drift"):
            MODULE.apply()


if __name__ == "__main__":
    unittest.main()
