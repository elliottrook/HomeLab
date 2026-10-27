#!/usr/bin/env python3
"""Unit tests for the bounded TrueNAS EPUB publication helper."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("epub_reader_exports.py")
SPEC = importlib.util.spec_from_file_location("epub_reader_exports", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.checkpoint = Path(self.temp.name) / "checkpoint"
        self.rows = []
        self.next_id = 40

    def api(self, method, *args):
        if method == "sharing.nfs.query":
            return list(self.rows)
        if method == "sharing.nfs.create":
            row = dict(args[0])
            row["id"] = self.next_id
            self.next_id += 1
            self.rows.append(row)
            return dict(row)
        if method == "sharing.nfs.delete":
            target = args[0]
            self.rows = [row for row in self.rows if row["id"] != target]
            return True
        if method == "sharing.nfs.update":
            target, values = args
            for index, row in enumerate(self.rows):
                if row["id"] == target:
                    updated = dict(values)
                    updated["id"] = target
                    self.rows[index] = updated
                    return dict(updated)
            raise AssertionError(target)
        raise AssertionError(method)

    def run_mode(self, mode):
        with mock.patch.object(MODULE, "CP", self.checkpoint), mock.patch.object(
            MODULE, "call", side_effect=self.api
        ), mock.patch.object(sys, "argv", ["epub_reader_exports.py", mode]):
            MODULE.main()

    def test_apply_verify_and_rollback_are_exact(self):
        self.run_mode("preview")
        self.run_mode("apply")
        self.assertEqual({row["path"] for row in self.rows}, set(MODULE.PATHS))
        self.assertTrue(all(row["ro"] for row in self.rows))
        self.assertTrue(all(row["hosts"] == [MODULE.HOST] for row in self.rows))
        self.assertTrue(all(row["maproot_user"] == "root" for row in self.rows))
        self.assertEqual(
            json.loads((self.checkpoint / "state.json").read_text()),
            {"absent": True, "paths": list(MODULE.PATHS), "schema": 1},
        )
        self.run_mode("verify")
        self.run_mode("rollback")
        self.assertEqual(self.rows, [])

    def test_existing_target_export_is_refused(self):
        self.rows.append(dict(MODULE.wanted(MODULE.PATHS[0]), id=10))
        with self.assertRaisesRegex(ValueError, "already-present"):
            self.run_mode("preview")

    def test_repairs_only_the_exact_root_squashed_predecessor(self):
        self.checkpoint.mkdir()
        (self.checkpoint / "state.json").write_text(json.dumps(
            {"absent": True, "paths": list(MODULE.PATHS), "schema": 1}))
        for identity, path in enumerate(MODULE.PATHS, 20):
            self.rows.append(dict(MODULE.legacy(path), id=identity))
        self.run_mode("repair")
        self.assertTrue(all(row["maproot_user"] == "root" for row in self.rows))
        self.run_mode("verify")


if __name__ == "__main__":
    unittest.main()
