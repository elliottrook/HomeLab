import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from lab_operations import Complete, Result, Start
from lab_operations_broker_gateway import GatewayServer, sanitize


class LabOperationsBrokerGatewayTests(unittest.TestCase):
    def setUp(self):
        self.peer_patch = patch(
            "lab_operations_broker_gateway.peer_uid", return_value=os.getuid(),
        )
        self.peer_patch.start()
        self.addCleanup(self.peer_patch.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.path = root / "gateway.sock"
        self.state = root / "jobs.db"
        self.owner = "a" * 64
        self.server = GatewayServer(
            str(self.path), state=self.state, owner=self.owner, broker_uid=os.getuid(),
        )
        self.server.store.claim()  # worker heartbeat only
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def call(self, request):
        with socket.socket(socket.AF_UNIX) as client:
            client.connect(str(self.path))
            client.sendall(json.dumps(request).encode() + b"\n")
            return json.loads(client.makefile("rb").readline())

    def request(self, method, arguments, request_id="01234567-89ab-cdef-0123-456789abcdef"):
        return {"method": method, "request_id": request_id, "arguments": arguments}

    def test_approved_shape_queues_only_doctor_and_latest_is_read_only(self):
        queued = self.call(self.request("doctor.run", {"purpose": "user_request"}))
        self.assertTrue(queued["ok"])
        self.assertEqual("doctor", queued["result"]["target"])
        self.assertEqual("queued", queued["result"]["state"])

        latest = self.call(self.request("doctor.latest", {}))
        self.assertTrue(latest["ok"])
        self.assertEqual(queued["result"]["id"], latest["result"]["id"])
        self.assertEqual("queued", self.server.store.get(self.owner)["state"])

    def test_replay_reuses_job_and_does_not_duplicate(self):
        request = self.request("doctor.run", {"purpose": "task_diagnosis"})
        first = self.call(request)
        second = self.call(request)
        self.assertTrue(first["ok"] and second["ok"])
        self.assertEqual(first["result"]["id"], second["result"]["id"])
        self.assertTrue(second["result"]["reused"])

    def test_schema_scope_and_peer_denials(self):
        denied = (
            self.request("doctor.run", {"purpose": "task_checkpoint"}),
            self.request("doctor.run", {"purpose": "user_request", "target": "nut"}),
            self.request("doctor.latest", {"target": "doctor"}),
            self.request("backup.run", {}),
            self.request("doctor.run", {"purpose": "user_request"}, "short"),
            {"method": "doctor.latest", "request_id": "0" * 32, "arguments": {}, "extra": True},
        )
        for request in denied:
            with self.subTest(request=request):
                self.assertFalse(self.call(request)["ok"])
        with patch("lab_operations_broker_gateway.peer_uid", return_value=os.getuid() + 1):
            self.assertFalse(self.call(self.request("doctor.latest", {}))["ok"])

    def test_stale_unrelated_job_blocks_without_reconciliation(self):
        with self.server.store.db() as database:
            database.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,'queued',NULL,NULL)",
                ("b" * 32, self.owner, "unrelated-backup-1", "nut", "user_request", 1, 1),
            )
        self.assertFalse(self.call(self.request("doctor.run", {"purpose": "user_request"}))["ok"])
        with self.server.store.db() as database:
            row = database.execute("SELECT state,result,updated FROM jobs WHERE id=?", ("b" * 32,)).fetchone()
        self.assertEqual(("queued", None, 1.0), tuple(row))

    def test_latest_stale_doctor_is_read_only(self):
        with self.server.store.db() as database:
            database.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,'queued',NULL,NULL)",
                ("c" * 32, self.owner, "stale-doctor-read", "doctor", "user_request", 1, 1),
            )
        latest = self.call(self.request("doctor.latest", {}))
        self.assertTrue(latest["ok"])
        self.assertTrue(latest["result"]["stale"])
        with self.server.store.db() as database:
            row = database.execute(
                "SELECT state,result,updated FROM jobs WHERE id=?", ("c" * 32,),
            ).fetchone()
        self.assertEqual(("queued", None, 1.0), tuple(row))

    def test_sanitizer_rejects_extra_or_unbounded_output(self):
        safe = {
            "id": "0" * 32, "target": "doctor", "purpose": "user_request",
            "created": 1, "updated": 1, "state": "succeeded", "reused": False,
            "result": {
                "state": "succeeded", "code": "checks_complete", "coverage": "diagnostic",
                "passed": 1, "warnings": 0, "failures": 0,
                "checks": [{"status": "pass", "summary": "bounded"}],
            },
        }
        self.assertEqual("doctor", sanitize(safe, now=1)["target"])
        for changed in (
            safe | {"raw_log": "secret"},
            safe | {"target": "nut"},
            safe | {"result": safe["result"] | {"token": "secret"}},
            safe | {"result": safe["result"] | {"checks": [{"status": "pass", "summary": "x\nleak"}]}},
            safe | {"result": safe["result"] | {"checks": [{"status": "fail", "summary": "token=secret"}]}},
        ):
            with self.assertRaises(Exception):
                sanitize(changed, now=1)


if __name__ == "__main__":
    unittest.main()
