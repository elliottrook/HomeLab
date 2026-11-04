import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v1 import run
from sa3_evidence_envelope_reconciliation_v1 import reconcile


PACKET = json.loads(
    Path(__file__).with_name("sa3-evidence-envelope-quality-v1.json").read_text()
)
BOOKING = "aster-stream-a-sa3-envelope-20261104-test"


def response(_payload):
    return {"choices": [{
        "message": {"role": "assistant", "content": json.dumps({
            "diagnosis": "The visible evidence supports a bounded statement.",
            "verification": "Refresh the registered evidence before cause.",
        })},
        "finish_reason": "stop",
    }]}


def result():
    return run(PACKET, response, model="hidden-model")


def terminal():
    return {
        "schema": "aster-lab-hours-booked-result.v1",
        "state": "complete", "booking_id": BOOKING,
        "started_epoch": 100, "finished_epoch": 200,
        "request_count": 20,
        "workload": "sa3-evidence-envelope-quality-v1",
        "production_restored": True,
    }


class EvidenceEnvelopeReconciliationTests(unittest.TestCase):
    def test_complete_transaction_builds_blind_pending_packet(self):
        summary, packet = reconcile(BOOKING, terminal(), PACKET, result())
        self.assertEqual("pending-independent-review", summary["quality_decision"])
        self.assertTrue(summary["production_restored"])
        self.assertFalse(summary["model_identity_disclosed"])
        self.assertNotIn("hidden-model", json.dumps(packet))

    def test_no_go_restoration_or_booking_drift_fails_closed(self):
        variants = []
        for field, changed in (
                ("state", "no_go"),
                ("production_restored", False),
                ("request_count", 14),
                ("booking_id", "other-booking")):
            value = copy.deepcopy(terminal())
            value[field] = changed
            variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                reconcile(BOOKING, value, PACKET, result())

    def test_result_error_fails_before_review_packet(self):
        value = result()
        value["errors"] = [{"id": value["predictions"][0]["id"],
                            "error_class": "TimeoutError"}]
        with self.assertRaises(ValueError):
            reconcile(BOOKING, terminal(), PACKET, value)

    def test_cli_writes_exclusive_blind_packet_and_content_free_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = {
                "terminal": terminal(), "packet": PACKET, "result": result(),
            }
            paths = {}
            for name, value in inputs.items():
                paths[name] = root / (name + ".json")
                paths[name].write_text(json.dumps(value), encoding="utf-8")
            output = root / "review.json"
            process = subprocess.run((sys.executable, "-B",
                str(Path(__file__).with_name("sa3_evidence_envelope_reconciliation_v1.py")),
                "--booking-id", BOOKING, "--terminal", str(paths["terminal"]),
                "--packet", str(paths["packet"]), "--result", str(paths["result"]),
                "--review-packet", str(output)), capture_output=True, text=True,
                check=False)
            self.assertEqual(0, process.returncode, process.stderr)
            summary = json.loads(process.stdout)
            self.assertEqual("pending-independent-review", summary["quality_decision"])
            self.assertNotIn("cases", summary)
            self.assertEqual(0o600, output.stat().st_mode & 0o777)
            self.assertFalse(json.loads(output.read_text())["model_identity_disclosed"])
            repeated = subprocess.run((sys.executable, "-B",
                str(Path(__file__).with_name("sa3_evidence_envelope_reconciliation_v1.py")),
                "--booking-id", BOOKING, "--terminal", str(paths["terminal"]),
                "--packet", str(paths["packet"]), "--result", str(paths["result"]),
                "--review-packet", str(output)), capture_output=True, text=True,
                check=False)
            self.assertNotEqual(0, repeated.returncode)


if __name__ == "__main__":
    unittest.main()

