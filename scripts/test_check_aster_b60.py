import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("check-aster-b60.sh")


class CheckAsterB60Tests(unittest.TestCase):
    def _stub(self, root: Path, name: str, body: str) -> None:
        path = root / name
        path.write_text("#!/bin/sh\nset -eu\n" + body)
        path.chmod(0o755)

    def test_accepts_current_sycl_service_and_never_invokes_vulkan(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._stub(root, "readlink", "printf '%s\\n' /sys/bus/pci/drivers/xe")
            self._stub(root, "qm", textwrap.dedent("""\
                if [ "$1" = status ]; then echo 'status: stopped'; exit; fi
                if [ "$1" = config ]; then exit; fi
                exit 2
            """))
            self._stub(root, "pct", textwrap.dedent("""\
                case "$*" in
                  'status 104'|'status 110') echo 'status: running' ;;
                  'exec 104 -- systemctl is-active --quiet aster-agent.service'|'exec 110 -- systemctl is-active --quiet aster-llama.service') exit 0 ;;
                  'exec 110 -- stat -c %t:%T:%G /dev/dri/renderD128') echo 'e2:80:render' ;;
                  'exec 110 -- systemctl show aster-llama.service -p Environment -p ExecStart -p ActiveState -p SubState -p NRestarts --no-pager') cat <<'EOF'
NRestarts=0
ExecStart=/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server -m /opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf --api-key-file /etc/aster-llama-api-keys
Environment=ONEAPI_DEVICE_SELECTOR=level_zero:gpu
ActiveState=active
SubState=running
EOF
                  ;;
                  'exec 110 -- curl --fail --silent --show-error --max-time 5 http://192.168.70.12:11435/health') echo '{"status":"ok"}' ;;
                  *vulkan*) echo forbidden-vulkan >&2; exit 99 ;;
                  *) echo "unexpected pct: $*" >&2; exit 98 ;;
                esac
            """))
            result = subprocess.run(
                ["/bin/sh", str(SCRIPT)], text=True, capture_output=True,
                env={**os.environ, "PATH": f"{root}:/usr/bin:/bin"},
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("accepted SYCL/Level Zero", result.stdout)
            self.assertNotIn("Vulkan visibility", result.stdout)


if __name__ == "__main__":
    unittest.main()
