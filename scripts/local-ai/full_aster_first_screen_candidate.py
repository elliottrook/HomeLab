"""Fixed transient-unit command boundary for the 35B first screen.

There is deliberately no CLI and no subprocess call.  A separately reviewed
root transaction may use these exact commands only after restart authority and
fresh same-cycle admission exist.
"""
from __future__ import annotations


UNIT = "aster-full-screen-qwen36.service"
BINARY = "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"
MODEL = "/opt/models/aster-first-screen/Qwen3.6-35B-A3B-Q4_K_M.gguf"
API_KEYS = "/etc/aster-llama-api-keys"
ENDPOINT = "192.168.70.12"
PORT = "11435"
LD_LIBRARY_PATH = (
    "/opt/aster-sycl-b11429/loader/usr/lib/x86_64-linux-gnu:"
    "/opt/aster-sycl-b11429/driver/usr/local/lib:"
    "/opt/aster-sycl-b11429/driver/usr/lib/x86_64-linux-gnu:"
    "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib:"
    "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib/clang/22/lib/x86_64-unknown-linux-gnu:"
    "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/dnnl/2026.0/lib:"
    "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/mkl/2026.1/lib:"
    "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/tbb/2023.1/lib:"
    "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/umf/1.1/lib:"
    "/opt/aster-sycl-b11429/oneapi/usr/lib/x86_64-linux-gnu"
)


def start_command() -> tuple[str, ...]:
    return (
        "pct", "exec", "110", "--", "/usr/bin/systemd-run", "--quiet",
        "--collect", f"--unit={UNIT}", "--property=Type=simple",
        "--property=User=ollama", "--property=Group=ollama",
        "--property=SupplementaryGroups=video render",
        "--property=Restart=no", "--property=TimeoutStartSec=330s",
        "--property=TimeoutStopSec=30s", "--property=NoNewPrivileges=yes",
        "--property=PrivateTmp=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes",
        "--property=RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX",
        "--property=LockPersonality=yes",
        f"--setenv=LD_LIBRARY_PATH={LD_LIBRARY_PATH}",
        "--setenv=ONEAPI_DEVICE_SELECTOR=level_zero:gpu",
        "--setenv=GGML_SYCL_ENABLE_FUSION=1",
        BINARY, "-m", MODEL, "-ngl", "999", "-c", "8192", "-np", "1",
        "-t", "4", "-tb", "4", "-b", "256", "-ub", "128", "-fa", "on",
        "-ctk", "q4_0", "-ctv", "q4_0", "--jinja", "--reasoning", "on",
        "--host", ENDPOINT, "--port", PORT, "--api-key-file", API_KEYS,
        "--metrics", "--log-verbosity", "4",
    )


def stop_command() -> tuple[str, ...]:
    return ("pct", "exec", "110", "--", "systemctl", "stop", UNIT)


def reset_failed_command() -> tuple[str, ...]:
    return ("pct", "exec", "110", "--", "systemctl", "reset-failed", UNIT)


def baseline_stop_command() -> tuple[str, ...]:
    return ("pct", "exec", "110", "--", "systemctl", "stop", "aster-llama.service")


def baseline_start_command() -> tuple[str, ...]:
    return ("pct", "exec", "110", "--", "systemctl", "start", "aster-llama.service")
