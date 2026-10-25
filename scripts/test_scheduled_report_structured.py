"""Offline integration test for the single-run scheduled Doctor producer."""

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parent
PRIVATE = "token=FIXTURE_NOT_A_SECRET private operator detail"


class ScheduledReportStructuredTests(unittest.TestCase):
    def test_one_doctor_run_feeds_report_sidecar_and_private_transcript(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scripts = root / "lab" / "homelab" / "scripts"
            scripts.mkdir(parents=True)
            shutil.copy2(SOURCE / "build-aster-health-report.py", scripts)
            shutil.copy2(SOURCE / "scheduled-report.sh", scripts)

            for name, body in (
                ("drift-check.sh", "#!/bin/bash\nprintf 'no drift\\n'\n"),
                ("certificate-check.sh", "#!/bin/bash\nprintf 'certificates ok\\n'\n"),
                ("backup-alert", "#!/bin/bash\nexit 99\n"),
            ):
                path = scripts / name
                path.write_text(body, encoding="utf-8")
                path.chmod(0o700)

            count = root / "doctor-count"
            doctor = scripts / "doctor.sh"
            doctor.write_text(
                "#!/bin/bash\n"
                "printf x >> \"$DOCTOR_COUNT\"\n"
                f"printf '🟢 {PRIVATE}\\n'\n"
                "printf '{\"run_id\":\"%s\",\"check_id\":\"aster.agent_inference\",\"state\":\"pass\"}\\n' "
                '"$DOCTOR_RUN_ID" >&"$DOCTOR_STRUCTURED_FD"\n',
                encoding="utf-8",
            )
            doctor.chmod(0o700)

            fake_bin = root / "bin"
            fake_bin.mkdir()
            published = root / "published.json"
            ssh = fake_bin / "ssh"
            ssh.write_text('#!/bin/sh\ncat > "$PUBLISH_CAPTURE"\n', encoding="utf-8")
            ssh.chmod(0o700)

            environment = os.environ.copy()
            environment.update({
                "HOME": str(root),
                "DOCTOR_COUNT": str(count),
                "PUBLISH_CAPTURE": str(published),
                "PATH": str(fake_bin) + os.pathsep + environment["PATH"],
            })
            result = subprocess.run(
                ["/bin/bash", str(scripts / "scheduled-report.sh")],
                capture_output=True, text=True, check=False, env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(count.read_text(), "x")

            state = root / "lab" / "monitoring-state" / "reports"
            aggregate_raw = (state / "aster-health.json").read_bytes()
            sidecar = json.loads((state / "aster-inference.json").read_text())
            self.assertEqual(sidecar["source_report_digest"], hashlib.sha256(aggregate_raw).hexdigest())
            self.assertEqual(sidecar["checks"], [{"check_id": "aster.agent_inference", "state": "pass"}])
            self.assertIn(PRIVATE, (state / "doctor-output.txt").read_text())
            self.assertNotIn(PRIVATE, json.dumps(sidecar))

            envelope = json.loads(published.read_text())
            self.assertEqual(base64.b64decode(envelope["aggregate"]), aggregate_raw)
            self.assertEqual(base64.b64decode(envelope["structured"]), (state / "aster-inference.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
