import importlib.util
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("astertv_beszel_register",
                                              HERE / "register_beszel_clients.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.executescript("""
      create table systems(created text not null, host text not null, id text primary key,
        info json, name text not null, port text not null, status text not null,
        updated text not null, users json not null);
      create table fingerprints(fingerprint text not null, id text primary key,
        system text not null, token text not null, updated text not null);
    """)
    return connection


class BeszelRegistrationTests(unittest.TestCase):
    def test_create_and_idempotent_rerun_preserve_tokens(self):
        connection = database()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = MODULE.register(connection, MODULE.TARGETS, '["owner"]', root)
            before = {path.name: path.read_text() for path in root.iterdir()}
            second = MODULE.register(connection, MODULE.TARGETS, '["owner"]', root)
            after = {path.name: path.read_text() for path in root.iterdir()}
            self.assertEqual({row["state"] for row in first.values()}, {"created"})
            self.assertEqual({row["state"] for row in second.values()}, {"existing"})
            self.assertEqual(before, after)
            self.assertEqual(connection.execute("select count(*) from systems").fetchone()[0], 3)
            self.assertEqual(connection.execute("select count(*) from fingerprints").fetchone()[0], 3)
            self.assertTrue(all((os.stat(path).st_mode & 0o777) == 0o600
                                for path in root.iterdir()))

    def test_conflicting_identity_is_rejected_without_extra_record(self):
        connection = database()
        connection.execute("insert into systems values(?,?,?,?,?,?,?,?,?)",
                           ("now", "192.168.1.99", "x", None, "AsterTV Bedroom",
                            "45876", "up", "now", '["owner"]'))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError, "identity-mismatch"):
                MODULE.register(connection, {"astertv-bedroom": MODULE.TARGETS["astertv-bedroom"]},
                                '["owner"]', Path(temporary))
        self.assertEqual(connection.execute("select count(*) from systems").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
