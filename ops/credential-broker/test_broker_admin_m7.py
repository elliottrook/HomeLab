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
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run(
                command[:-1] + ["graduate-lab-doctor"], check=True, capture_output=True, text=True,
            )
            store = BrokerStore(database)
            self.assertEqual("healthy", store.connection.execute(
                "SELECT health FROM services WHERE service_id='lab-operations'"
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

    def test_fixed_doctor_enrollment_is_single_grant_and_reversible(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "broker.db"
            command = [
                sys.executable, str(Path(__file__).with_name("broker_admin.py")),
                "--database", str(database), "enable-fixed-doctor", "--agent-uid", "1905",
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run(command, check=True, capture_output=True, text=True)
            store = BrokerStore(database)
            self.assertEqual((1905, "observer"), tuple(store.connection.execute(
                "SELECT unix_uid,state FROM agents WHERE agent_id='agent-aster-fixed-doctor'"
            ).fetchone()))
            self.assertEqual([
                ("diagnostic.aster-inference.latest",),
            ], [tuple(row) for row in store.connection.execute(
                "SELECT capability FROM agent_capabilities WHERE agent_id='agent-aster-fixed-doctor'"
            ).fetchall()])
            self.assertEqual(("aster-fixed-doctor", "green", 0, 1), tuple(store.connection.execute(
                "SELECT service_id,risk_class,probation_allowed,enabled FROM capabilities "
                "WHERE capability='diagnostic.aster-inference.latest'"
            ).fetchone()))
            store.close()

            subprocess.run(
                command[:4] + ["disable-fixed-doctor"],
                check=True, capture_output=True, text=True,
            )
            store = BrokerStore(database)
            self.assertEqual("suspended", store.connection.execute(
                "SELECT state FROM agents WHERE agent_id='agent-aster-fixed-doctor'"
            ).fetchone()[0])
            self.assertEqual(0, store.connection.execute(
                "SELECT enabled FROM services WHERE service_id='aster-fixed-doctor'"
            ).fetchone()[0])
            self.assertEqual(0, store.connection.execute(
                "SELECT count(*) FROM agent_capabilities WHERE agent_id='agent-aster-fixed-doctor'"
            ).fetchone()[0])
            store.close()

    def test_fixed_doctor_enrollment_refuses_other_grant(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "broker.db"
            store = BrokerStore(database)
            store.register_agent("agent-aster-fixed-doctor", 1905)
            store.set_agent_state("agent-aster-fixed-doctor", "observer")
            store.register_service("other")
            store.register_capability("other.read", "other", "green")
            store.grant_capability("agent-aster-fixed-doctor", "other.read")
            store.close()
            completed = subprocess.run([
                sys.executable, str(Path(__file__).with_name("broker_admin.py")),
                "--database", str(database), "enable-fixed-doctor", "--agent-uid", "1905",
            ], capture_output=True, text=True)
            self.assertNotEqual(0, completed.returncode)
            store = BrokerStore(database)
            self.assertIsNone(store.connection.execute(
                "SELECT 1 FROM services WHERE service_id='aster-fixed-doctor'"
            ).fetchone())
            store.close()


if __name__ == "__main__":
    unittest.main()
