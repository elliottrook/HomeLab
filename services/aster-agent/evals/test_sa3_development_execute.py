import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from sa3_development_execute import (
    journal_status_counts,
    main,
    read_api_key_from_fd,
    run_spec,
)


class DevelopmentExecuteTests(unittest.TestCase):
    def setUp(self):
        self.here = Path(__file__).parent
        self.fixtures = self.here / "sysadmin-sa3-development-fixtures-draft-v1.json"
        self.source = self.here / "sysadmin-incident-development-extension-draft-v1.json"
        self.plan = self.here / "sysadmin-incident-development-plan-v1.json"

    def test_dry_run_is_qualified_content_free_and_credential_free(self):
        command = [sys.executable, str(self.here / "sa3_development_execute.py")]
        result = subprocess.run(command, env={}, capture_output=True, text=True, check=True)
        value = json.loads(result.stdout)
        self.assertEqual(value["status"], "dry_run_valid")
        self.assertEqual(value["run_spec"]["cases"], 12)
        self.assertEqual(value["run_spec"]["sessions"], 12)
        self.assertEqual(value["run_spec"]["maximum_model_calls"], 36)
        self.assertEqual(value["run_spec"]["request_timeout_seconds"], 60)
        self.assertEqual(value["run_spec"]["mode"], "nonthinking")
        self.assertFalse(value["run_spec"]["connected_tools"])
        self.assertFalse(value["run_spec"]["effects"])
        self.assertEqual(len(value["run_spec"]["implementation_sha256"]), 8)
        self.assertTrue(all(
            len(item) == 64
            for item in value["run_spec"]["implementation_sha256"].values()
        ))
        self.assertFalse(value["keys_accessed"])

    def test_run_spec_is_bound_to_fixture_and_sources(self):
        spec = run_spec(self.fixtures, self.source, self.plan)
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "fixtures.json"
            changed.write_bytes(self.fixtures.read_bytes() + b" ")
            self.assertNotEqual(
                spec["fixture_file_sha256"],
                run_spec(changed, self.source, self.plan)["fixture_file_sha256"],
            )

    def test_current_candidate_source_manifest_matches_exact_dry_run(self):
        manifest = json.loads((
            self.here / "sa3-development-attempt-11-source-manifest.json"
        ).read_text())
        self.assertEqual("candidate-H", manifest["candidate_alias"])
        self.assertEqual("not-granted", manifest["authority"])
        spec = run_spec(self.fixtures, self.source, self.plan)
        from sa3_fresh_package import digest
        self.assertEqual(digest(spec), manifest["run_digest"])
        names = [row["name"] for row in manifest["files"]]
        expected = list(spec["implementation_sha256"]) + [
            self.fixtures.name, self.source.name, self.plan.name,
        ]
        self.assertEqual(expected, names)
        for row in manifest["files"]:
            raw = (self.here / row["name"]).read_bytes()
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_frozen_implementation_set_is_import_complete(self):
        spec = run_spec(self.fixtures, self.source, self.plan)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in spec["implementation_sha256"]:
                shutil.copy2(self.here / name, root / name)
            for path in (self.fixtures, self.source, self.plan):
                shutil.copy2(path, root / path.name)
            result = subprocess.run(
                [sys.executable, str(root / "sa3_development_execute.py")],
                cwd=root,
                env={},
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(result.stdout)["status"], "dry_run_valid")

    def test_execute_requires_exact_digest_before_authentication(self):
        with self.assertRaisesRegex(SystemExit, "approved digest"):
            main(["--execute", "--expected-run-digest", "0" * 64])

    def test_dry_run_does_not_touch_key_descriptor(self):
        result = subprocess.run(
            [sys.executable, str(self.here / "sa3_development_execute.py"),
             "--key-fd", "9999"],
            env={"ASTER_LLAMA_API_KEY": "must-not-be-used"},
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertFalse(json.loads(result.stdout)["keys_accessed"])

    def test_descriptor_key_is_bounded_and_closed(self):
        read_fd, write_fd = os.pipe()
        os.write(write_fd, b"fictional-local-key\n")
        os.close(write_fd)
        self.assertEqual("fictional-local-key", read_api_key_from_fd(read_fd))
        with self.assertRaises(OSError):
            os.fstat(read_fd)

    def test_descriptor_rejects_stdio_and_oversized_or_invalid_keys(self):
        with self.assertRaisesRegex(SystemExit, "descriptor required"):
            read_api_key_from_fd(0)
        for value, message in (
                (b"x" * 4097, "bounded size"),
                (b"contains space", "invalid encoding"),
                (b"", "invalid encoding")):
            read_fd, write_fd = os.pipe()
            os.write(write_fd, value)
            os.close(write_fd)
            with self.assertRaisesRegex(SystemExit, message):
                read_api_key_from_fd(read_fd)

    def test_journal_status_projection_is_content_free(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            path.write_text("\n".join((
                json.dumps({"event": {"type": "started"}}),
                json.dumps({"event": {"type": "finished", "result": {"status": "clarify", "summary": "private"}}}),
                json.dumps({"event": {"type": "finished", "result": {"status": "invalid_answer"}}}),
            )) + "\n")
            self.assertEqual(
                journal_status_counts(path),
                {"clarify": 1, "invalid_answer": 1},
            )


if __name__ == "__main__":
    unittest.main()
