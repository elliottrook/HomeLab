import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


MODULE_PATH = Path(__file__).with_name("expand_onkyo_firewall_udp.py")
SPEC = importlib.util.spec_from_file_location("expand_onkyo_firewall_udp", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExpandOnkyoFirewallUdpTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = root / "config.xml"
        self.checkpoint = root / "checkpoint.xml"
        self.proof = root / "proof.json"
        self.before = b"""<opnsense><filter><rules>
<rule uuid="af4ef3e0-e9ad-45c7-b2a7-2fe59cb50cff">
<enabled>1</enabled><sequence>1852</sequence><action>pass</action>
<interface>opt3</interface><direction>in</direction><ipprotocol>inet</ipprotocol>
<protocol>TCP</protocol><source_net>192.168.20.11</source_net><source_not>0</source_not>
<destination_net>192.168.1.186</destination_net><destination_not>0</destination_not>
<destination_port>60128</destination_port>
<description>AsterTV M7 HA to Family Onkyo native control</description>
</rule></rules></filter></opnsense>"""
        self.config.write_bytes(self.before)
        MODULE.CONFIG = self.config
        MODULE.CHECKPOINT = self.checkpoint
        MODULE.PROOF = self.proof
        MODULE.EXPECTED = hashlib.sha256(self.before).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def test_apply_and_exact_rollback(self):
        MODULE.apply()
        rule = next(iter(ET.parse(self.config).getroot().iter("rule")))
        self.assertEqual(rule.findtext("protocol"), "TCP/UDP")
        MODULE.rollback()
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_rule_drift_fails_closed(self):
        root = ET.parse(self.config)
        next(iter(root.getroot().iter("rule"))).find("destination_port").text = "80"
        root.write(self.config, encoding="utf-8")
        MODULE.EXPECTED = hashlib.sha256(self.config.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError, "tcp-rule-drift"):
            MODULE.apply()


if __name__ == "__main__":
    unittest.main()
