import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class ExerciseOwnerStartTests(unittest.TestCase):
    def wrapper_source(self):
        return (Path(__file__).resolve().parents[2] / "services/local-ai-lease" /
                "stream-a-evaluation-exercise-owner-start")

    def test_wrapper_is_inert_without_exact_authorization(self):
        for arguments in ((), ("--wrong",), ("--effect-authorized", "extra")):
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    ("/bin/sh", str(self.wrapper_source()), *arguments), check=True,
                    capture_output=True, text=True,
                )
                self.assertEqual(json.loads(result.stdout),
                                 {"effects": "disabled", "state": "source-only"})

    def test_authorized_wrapper_pins_transient_unit_hardening_and_owner_flags(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            capture = root / "systemd-run"
            capture.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
            capture.chmod(0o755)
            wrapper = root / "wrapper"
            wrapper.write_text(self.wrapper_source().read_text().replace(
                "/usr/bin/systemd-run", str(capture)))
            wrapper.chmod(0o755)
            result = subprocess.run(
                ("/bin/sh", str(wrapper), "--effect-authorized"), check=True,
                capture_output=True, text=True,
            )
            self.assertEqual(result.stdout.splitlines(), [
                "--unit=stream-a-evaluation-exercise-owner.service",
                "--collect",
                "--service-type=simple",
                "--property=User=root",
                "--property=NoNewPrivileges=yes",
                "--property=ProtectSystem=strict",
                "--property=ProtectHome=yes",
                "--property=PrivateTmp=yes",
                "--property=ReadWritePaths=/etc/local-ai-lab/stream-a-evaluation",
                "--property=ReadWritePaths=/var/lib/local-ai-lab/stream-a-evaluation",
                "/usr/local/sbin/stream-a-evaluation-owner",
                "--run",
                "--effect-authorized",
                "--exercise-transient",
            ])


if __name__ == "__main__":
    unittest.main()
