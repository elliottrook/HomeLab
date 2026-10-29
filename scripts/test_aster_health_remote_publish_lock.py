import ast
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER = Path(__file__).with_name("build-aster-health-report.py")


def writer_source(root: Path) -> str:
    tree = ast.parse(BUILDER.read_text())
    values = [
        node.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "writer" for target in node.targets)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(values) != 1:
        raise AssertionError("remote writer source not found")
    source = values[0].replace("'/var/lib/aster/health'", repr(str(root)))
    source = source.replace("gid=grp.getgrnam('aster').gr_gid", "gid=os.getgid()")
    source = source.replace("lock_stat.st_uid==0", "lock_stat.st_uid==os.geteuid()")
    source = source.replace("os.fchown(lock_fd,0,gid)", "os.fchown(lock_fd,os.geteuid(),gid)")
    source = source.replace("os.chown(temporary,0,gid)", "os.chown(temporary,os.geteuid(),gid)")
    return source


def envelope(label: str) -> str:
    generated = f"2026-10-29T03:30:{label}Z"
    aggregate = json.dumps({
        "schema": 1,
        "generated_at": generated,
        "status": "warning",
        "checks": [{"name": "fixture", "status": "warn", "summary": label}],
    }, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    digest = hashlib.sha256(aggregate).hexdigest()
    run_id = (label * 32)[:32]
    structured = json.dumps({
        "schema": 2, "generated_at": generated, "run_id": run_id,
        "source_report_digest": digest,
        "checks": [{"check_id": "aster.agent_inference", "state": "warn"}],
    }, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    catalogue = json.dumps({
        "schema": 3, "generated_at": generated, "run_id": run_id,
        "source_report_digest": digest,
        "checks": [
            {"check_id": "aster.agent_inference", "state": "warn"},
            {"check_id": "aster.speech", "state": "pass"},
            {"check_id": "backup.protection", "state": "pass"},
        ],
    }, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    return json.dumps({
        "aggregate": base64.b64encode(aggregate).decode(),
        "structured": base64.b64encode(structured).decode(),
        "catalogue": base64.b64encode(catalogue).decode(),
    })


class RemotePublishLockTests(unittest.TestCase):
    def test_concurrent_writers_leave_one_coherent_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "health"
            source = writer_source(root)
            for left, right in (("11", "22"), ("33", "44"), ("55", "66"), ("77", "88")):
                processes = [
                    subprocess.Popen(
                        [sys.executable, "-c", source], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    )
                    for _ in range(2)
                ]
                for process, payload in zip(processes, (envelope(left), envelope(right))):
                    _, error = process.communicate(payload, timeout=10)
                    self.assertEqual(process.returncode, 0, error)
                aggregate = (root / "latest.json").read_bytes()
                structured = json.loads((root / "aster-inference.json").read_text())
                catalogue = json.loads((root / "diagnostic-catalogue.json").read_text())
                digest = hashlib.sha256(aggregate).hexdigest()
                self.assertEqual(structured["source_report_digest"], digest)
                self.assertEqual(catalogue["source_report_digest"], digest)
                self.assertEqual(structured["run_id"], catalogue["run_id"])
                self.assertEqual(structured["generated_at"], catalogue["generated_at"])
            self.assertEqual((root / ".publisher.lock").stat().st_mode & 0o777, 0o640)


if __name__ == "__main__":
    unittest.main()
