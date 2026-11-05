import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


MODULE_PATH = Path(__file__).with_name("reserve_family_tcl.py")
SPEC = importlib.util.spec_from_file_location("reserve_family_tcl", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReserveFamilyTclTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = root / "config.xml"
        self.checkpoint = root / "checkpoint.xml"
        self.proof = root / "proof.json"
        self.before = b"""<opnsense><dnsmasq>
<hosts uuid="ebc4a8d7-aaa4-42e3-8245-090600d0d6a2">
<host>philips-hue</host><domain/><local>0</local><ip>192.168.30.164</ip>
<cnames/><client_id/><hwaddr>00:17:88:22:42:e5</hwaddr><lease_time/>
<ignore>0</ignore><set_tag/><descr>Philips Hue Bridge</descr><comments/><aliases/>
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
        hosts = list(ET.parse(self.config).getroot().findall("dnsmasq/hosts"))
        self.assertEqual(len(hosts), 2)
        self.assertEqual(hosts[1].findtext("host"), "family-room-tv")
        self.assertEqual(hosts[1].findtext("ip"), "192.168.30.162")
        self.assertEqual(hosts[1].findtext("hwaddr"), "0c:91:60:75:7c:5c")
        MODULE.rollback()
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_identity_collision_fails_closed(self):
        tree = ET.parse(self.config)
        tree.getroot().find("dnsmasq/hosts/ip").text = "192.168.30.162"
        tree.write(self.config, encoding="utf-8")
        MODULE.EXPECTED = hashlib.sha256(self.config.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError, "identity-collision"):
            MODULE.apply()


if __name__ == "__main__":
    unittest.main()
