import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v2 import run
from sa3_evidence_envelope_reconciliation_v2 import reconcile


ROOT = Path(__file__).parent
PACKET = json.loads((ROOT / "sa3-evidence-envelope-candidate-i-quality-v1.json").read_text())
BOOKING = "aster-stream-a-sa3-candidate-i-20261104-test"


def response(_payload):
    return {"choices": [{"message": {"role": "assistant", "content": json.dumps({
        "diagnosis": "The visible evidence supports a bounded diagnosis."
    })}, "finish_reason": "stop"}]}


def result():
    return run(PACKET, response, model="hidden-model")


def terminal():
    return {
        "schema": "aster-lab-hours-booked-result.v1", "state": "complete",
        "booking_id": BOOKING, "started_epoch": 100, "finished_epoch": 200,
        "request_count": 20,
        "workload": "sa3-evidence-envelope-candidate-i-quality-v1",
        "production_restored": True,
    }


class EvidenceEnvelopeReconciliationV2Tests(unittest.TestCase):
    def test_complete_transaction_builds_blind_pending_packet(self):
        summary, packet = reconcile(BOOKING, terminal(), PACKET, result())
        self.assertEqual("pending-three-independent-reviews",
                         summary["quality_decision"])
        self.assertEqual(6, summary["deterministic_abstentions"])
        self.assertNotIn("hidden-model", json.dumps(packet))

    def test_no_go_restoration_booking_or_workload_drift_fails(self):
        for field, changed in (("state", "no_go"),
                               ("production_restored", False),
                               ("request_count", 14),
                               ("booking_id", "other"),
                               ("workload", "other")):
            value = copy.deepcopy(terminal()); value[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                reconcile(BOOKING, value, PACKET, result())

    def test_cli_is_exclusive_and_summary_is_content_free(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); paths = {}
            for name, value in (("terminal", terminal()), ("packet", PACKET),
                                ("result", result())):
                paths[name] = root / f"{name}.json"
                paths[name].write_text(json.dumps(value), encoding="utf-8")
            output = root / "review.json"
            command = (sys.executable, "-B", str(ROOT /
                "sa3_evidence_envelope_reconciliation_v2.py"),
                "--booking-id", BOOKING, "--terminal", str(paths["terminal"]),
                "--packet", str(paths["packet"]), "--result", str(paths["result"]),
                "--review-packet", str(output))
            process = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertNotIn("cases", json.loads(process.stdout))
            self.assertEqual(0o600, output.stat().st_mode & 0o777)
            self.assertNotEqual(0, subprocess.run(
                command, capture_output=True, text=True).returncode)


if __name__ == "__main__":
    unittest.main()
