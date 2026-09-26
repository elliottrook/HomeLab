import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from broker_core import BrokerStore


class BrokerAdminM7Tests(unittest.TestCase):
    def test_enable_is_idempotent_and_disable_revokes_service(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "broker.db"
            store = BrokerStore(database)
            store.register_agent("agent-hermes", 1234)
            store.set_agent_state("agent-hermes", "operator")
            store.close()
            command = [
                sys.executable, str(Path(__file__).with_name("broker_admin.py")),
                "--database", str(database), "enable-lab-doctor",
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run(command, check=True, capture_output=True, text=True)
            store = BrokerStore(database)
            self.assertEqual(1, store.connection.execute(
                "SELECT count(*) FROM services WHERE service_id='lab-operations' AND enabled=1"
            ).fetchone()[0])
            self.assertEqual(2, store.connection.execute(
                "SELECT count(*) FROM capabilities WHERE service_id='lab-operations' AND enabled=1"
            ).fetchone()[0])
            self.assertEqual(2, store.connection.execute(
                "SELECT count(*) FROM agent_capabilities WHERE agent_id='agent-hermes' AND capability LIKE 'lab.doctor.%'"
            ).fetchone()[0])
            store.close()
            subprocess.run(command[:-1] + ["disable-lab-doctor"], check=True, capture_output=True, text=True)
            store = BrokerStore(database)
            self.assertEqual(0, store.connection.execute(
                "SELECT enabled FROM services WHERE service_id='lab-operations'"
            ).fetchone()[0])
            store.close()

    def test_enable_refuses_conflicting_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "broker.db"
            store = BrokerStore(database)
            store.register_agent("agent-hermes", 1234)
            store.register_service("conflicting")
            store.register_capability("lab.doctor.latest", "conflicting", "red")
            store.close()
            completed = subprocess.run([
                sys.executable, str(Path(__file__).with_name("broker_admin.py")),
                "--database", str(database), "enable-lab-doctor",
            ], capture_output=True, text=True)
            self.assertNotEqual(0, completed.returncode)
            store = BrokerStore(database)
            row = store.connection.execute(
                "SELECT service_id,risk_class FROM capabilities WHERE capability='lab.doctor.latest'"
            ).fetchone()
            self.assertEqual(("conflicting", "red"), tuple(row))
            self.assertIsNone(store.connection.execute(
                "SELECT 1 FROM services WHERE service_id='lab-operations'"
            ).fetchone())
            store.close()


if __name__ == "__main__":
    unittest.main()
