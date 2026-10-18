"""Fixed final restoration validator for the full-inference drain candidate."""

from __future__ import annotations

import json
import os
from typing import Callable, Sequence

from full_inference_lab_sources import AcceptedBaseline, FIXED

Runner = Callable[[Sequence[str], float], tuple[int, str]]


class FullDrainValidator:
    def __init__(self, runner: Runner, baseline: AcceptedBaseline):
        self.runner, self.baseline = runner, baseline

    def _run(self, command: Sequence[str], timeout: float = 10.0) -> str:
        code, output = self.runner(command, timeout)
        if code != 0:
            raise ValueError("final validator probe failed")
        return output.strip()

    def _hash(self, vmid: str, path: str, expected: str) -> None:
        if self._run(("pct", "exec", vmid, "--", "sha256sum", path), 30.0).split()[:1] != [expected]:
            raise ValueError("accepted baseline hash mismatch")

    def __call__(self) -> bool:
        try:
            driver = self._run(FIXED["driver"])
            if not (driver.rstrip("/").endswith("/bus/pci/drivers/xe") or os.path.basename(driver.rstrip("/")) == "xe"):
                return False
            if "status: stopped" not in self._run(FIXED["vm"]):
                return False
            if "04:00.0" in self._run(FIXED["vm_config"]):
                return False
            pve = json.loads(self._run(FIXED["schedules"]))
            truenas = json.loads(self._run(FIXED["truenas"]))
            if not isinstance(pve, list) or not pve:
                return False
            for item_id in (1, 2, 3):
                item = next((x for x in truenas if x.get("id") == item_id), None)
                if not item or not item.get("enabled") or item.get("job", {}).get("state") != "SUCCESS":
                    return False
            self._hash("110", "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf", self.baseline.model_sha256)
            self._hash("110", "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server", self.baseline.binary_sha256)
            self._hash("110", "/etc/systemd/system/aster-llama.service", self.baseline.unit_sha256)
            for vmid, unit in (("110", "aster-llama.service"), ("116", "aster-speech.service"), ("104", "aster-agent.service")):
                if self._run(("pct", "exec", vmid, "--", "systemctl", "is-active", unit), 5.0) != "active":
                    return False
            for key in ("news_ingest_active", "news_digest_active"):
                if self._run(FIXED[key]) != "active":
                    return False
            for key in ("news_ingest_enabled", "news_digest_enabled"):
                if self._run(FIXED[key]) != "enabled":
                    return False
            self._run(FIXED["auth"], 15.0)
            return True
        except (OSError, ValueError, json.JSONDecodeError):
            return False
