import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name("provision_remote_voice_proxy.mjs").read_text()


class RemoteVoiceProxyTests(unittest.TestCase):
    def test_route_is_additive_and_mac_backed(self):
        self.assertIn('path: "/voice/v3/"', SOURCE)
        self.assertIn('forward_host: "192.168.20.37"', SOURCE)
        self.assertIn('forward_port: 9131, forward_path: "/"', SOURCE)
        self.assertIn("[canonical, ...locations]", SOURCE)

    def test_legacy_and_streaming_predecessors_are_preserved(self):
        self.assertIn('path: "/voice/"', SOURCE)
        self.assertIn('forward_host: "192.168.70.14"', SOURCE)
        self.assertIn('path: "/voice/v2/"', SOURCE)
        self.assertIn('forward_path: "/v2/"', SOURCE)
        self.assertNotIn("filter(location => location.path !==", SOURCE)

    def test_dry_run_and_exact_host_gates_exist(self):
        self.assertIn('process.argv.includes("--apply")', SOURCE)
        self.assertIn("host.id !== 18", SOURCE)
        self.assertIn('host.forward_host !== "192.168.70.10"', SOURCE)
        self.assertIn("accepted voice predecessor drift", SOURCE)
        self.assertIn("unexpected /voice/v3/ location", SOURCE)


if __name__ == "__main__":
    unittest.main()
