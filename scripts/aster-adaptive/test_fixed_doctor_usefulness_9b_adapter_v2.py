import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness as usefulness
import fixed_doctor_usefulness_9b_adapter_v2 as adapter


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"


class FixedDoctorUsefulness9BAdapterV2Tests(unittest.TestCase):
    def case(self):
        fixture = usefulness.load_unique(FIXTURE.read_bytes())
        usefulness.validate(fixture)
        return fixture["cases"][3]

    def test_prompt_requires_explicit_cause_and_repair_limitation(self):
        body = json.loads(adapter.request_for(self.case(), "test-only-key").data)
        system = body["messages"][0]["content"]
        self.assertIn("cannot establish a cause or a repair", system)
        self.assertIn("only the named Aster inference check", system)
        self.assertNotIn("expected", body["messages"][1]["content"])
        self.assertNotIn("tools", body)

    def test_v2_retains_fixed_local_transport_boundary(self):
        request = adapter.request_for(self.case(), "test-only-key")
        body = json.loads(request.data)
        self.assertEqual("http://192.168.70.12:11435/v1/chat/completions", request.full_url)
        self.assertEqual("aster-qwen3.5-9b", body["model"])
        self.assertEqual(0, body["temperature"])
        self.assertEqual(256, body["max_tokens"])


if __name__ == "__main__":
    unittest.main()
