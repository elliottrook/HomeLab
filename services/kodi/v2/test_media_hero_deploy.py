import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "deploy_media_hero", Path(__file__).parent / "tools/deploy_media_hero.py")
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class MediaHeroDeployTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        staging = root / "staging"; staging.mkdir()
        checkpoints = root / "checkpoints"; checkpoints.mkdir()
        stage = staging / deploy.STAGE_NAME; stage.mkdir()
        targets = {}
        rows = []
        for index, name in enumerate(deploy.EXPECTED_TARGETS):
            target = root / "installed" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            before = (("before_%d = True\n" % index).encode() if name.endswith(".py")
                      else ("<window id=\"%d\"/>\n" % index).encode())
            after = (("after_%d = True\n" % index).encode() if name.endswith(".py")
                     else ("<window id=\"%d\"><controls/></window>\n" % index).encode())
            target.write_bytes(before)
            source = stage / name; source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(after)
            targets[name] = str(target)
            rows.append({"path": name, "target": str(target),
                         "sha256": hashlib.sha256(after).hexdigest(),
                         "previous_sha256": hashlib.sha256(before).hexdigest()})
        raw = (json.dumps({"schema": 1,
                           "kind": "hp-media-recommendation-hero",
                           "stage": deploy.STAGE_NAME, "files": rows},
                          indent=2) + "\n").encode()
        (stage / "manifest.json").write_bytes(raw)
        values = (("STAGING", staging), ("CHECKPOINTS", checkpoints),
                  ("RECOVERY", root / "recovery"),
                  ("EXPECTED_TARGETS", targets),
                  ("CANDIDATE_MANIFEST", hashlib.sha256(raw).hexdigest()))
        for name, value in values:
            mocked = patch.object(deploy, name, value); mocked.start(); self.addCleanup(mocked.stop)
        mocked = patch.object(deploy.os, "uname",
                              return_value=SimpleNamespace(nodename="AsterTV"))
        mocked.start(); self.addCleanup(mocked.stop)
        mocked = patch.object(deploy, "active_players")
        mocked.start(); self.addCleanup(mocked.stop)
        mocked = patch.object(deploy.subprocess, "run",
                              return_value=SimpleNamespace(returncode=0))
        mocked.start(); self.addCleanup(mocked.stop)
        self.rows = {row["path"]: row for row in rows}

    def test_install_and_exact_rollback(self):
        deploy.install()
        for row in self.rows.values():
            self.assertEqual(deploy.digest(row["target"]), row["sha256"])
        deploy.rollback()
        for row in self.rows.values():
            self.assertEqual(deploy.digest(row["target"]), row["previous_sha256"])

    def test_unknown_predecessor_is_refused_before_stop(self):
        first = next(iter(self.rows.values()))
        Path(first["target"]).write_text("unknown")
        with self.assertRaisesRegex(RuntimeError, "predecessor-drift"):
            deploy.install()
        deploy.subprocess.run.assert_not_called()

    def test_rollback_refuses_installed_drift(self):
        deploy.install()
        first = next(iter(self.rows.values()))
        Path(first["target"]).write_text("unknown")
        with self.assertRaisesRegex(RuntimeError, "installed-drift"):
            deploy.rollback()


if __name__ == "__main__":
    unittest.main()
