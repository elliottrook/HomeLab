#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("check_ai_pam", Path(__file__).with_name("check-ai-pam.py"))
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def healthy():
    return {
        "integrity": "ok", "global_enabled": "1",
        "services": [[name, 1] for name in sorted(module.EXPECTED_SERVICES)],
        "capabilities": [[name, service, risk, 1] for name, (service, risk) in sorted(module.EXPECTED_CAPABILITIES.items())],
        "agents": [["agent-hermes", "operator"], ["agent-replacement-m5", "retired"]],
        "active_requests": 0, "expired_active": 0,
        "services_active": {"unit": True},
        "sockets": {"socket": {"socket": True, "mode": 0o660, "uid": 1, "gid": 2}},
        "openbao": {"reachable": True, "sealed": False, "initialized": True},
    }


class CheckAIPAMTests(unittest.TestCase):
    def test_healthy_exact_policy(self):
        self.assertEqual(0, module.classify(healthy())[0])

    def test_global_disable_fails(self):
        data = healthy(); data["global_enabled"] = "0"
        self.assertIn("global access disabled", module.classify(data)[1])

    def test_catalogue_expansion_is_drift(self):
        data = healthy(); data["capabilities"].append(["unreviewed", "synthetic", "green", 1])
        self.assertIn("capability catalogue drift", module.classify(data)[1])

    def test_sealed_openbao_fails(self):
        data = healthy(); data["openbao"]["sealed"] = True
        self.assertIn("OpenBao unavailable or sealed", module.classify(data)[1])

    def test_expired_active_request_fails(self):
        data = healthy(); data["expired_active"] = 1
        self.assertIn("expired active requests", module.classify(data)[1])


if __name__ == "__main__":
    unittest.main()
