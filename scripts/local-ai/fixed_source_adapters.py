"""Fixed-command source adapters for authenticated lease receipts."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from datetime import datetime

from admission_gate import EXPECTED_BACKUP_SOURCE, AdmissionEvidenceError
from backup_receipt_adapter import verify_lxc110_mirror, verify_proxmox_artifacts
from quiescence_receipt_adapter import ConsumerSnapshot, compose_quiescence_receipt
from source_receipts import BackupSourceReceipt, QuiescenceSourceReceipt, compose_candidate_evidence

Runner = Callable[[tuple[str, ...], float], tuple[int, str]]

PRODUCTION = (("104", "aster-agent.service"), ("110", "aster-llama.service"), ("116", "aster-speech.service"))
TRUENAS = "aster-schedule-observer@192.168.20.40"
KNOWN_HOSTS = "/etc/local-ai-lab/truenas_known_hosts"
IDENTITY = "/etc/local-ai-lab/truenas_schedule_observer"


class SourceAdapterError(ValueError):
    pass


def _json(runner: Runner, argv: tuple[str, ...], timeout: float = 30.0):
    code, output = runner(argv, timeout)
    if code != 0:
        raise SourceAdapterError("fixed source command failed")
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise SourceAdapterError("fixed source returned invalid JSON") from exc


def _truenas(command: tuple[str, ...]) -> tuple[str, ...]:
    return ("ssh", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={KNOWN_HOSTS}", "-i", IDENTITY, TRUENAS, *command)


def _schedule_ok(items: list[dict]) -> bool:
    expected = {1: (1, "01:00"), 3: (3, "02:00"), 2: (2, "03:00")}
    for item_id, (_, clock) in expected.items():
        item = next((item for item in items if item.get("id") == item_id), None)
        schedule = item.get("schedule", {}) if item else {}
        if not item or not item.get("enabled") or f"{int(schedule.get('hour', -1)):02d}:{int(schedule.get('minute', -1)):02d}" != clock:
            return False
        if item.get("job", {}).get("state") != "SUCCESS":
            return False
    return True


class FixedSourceAdapters:
    def __init__(self, runner: Runner, *, sleep: Callable[[float], None] = time.sleep, clock: Callable[[], datetime] = datetime.now, monotonic: Callable[[], int] = time.monotonic_ns):
        self.runner, self.sleep, self.clock, self.monotonic = runner, sleep, clock, monotonic

    def backup(self, *, date_prefix: str, verify_archives: bool = True) -> BackupSourceReceipt:
        pve = _json(self.runner, ("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json"), 30.0)
        artifacts = verify_proxmox_artifacts(pve, date_prefix=date_prefix)
        rsync = _json(self.runner, _truenas(("midclt", "call", "rsynctask.query")), 10.0)
        if not _schedule_ok(rsync):
            raise SourceAdapterError("TrueNAS backup tasks are not all successful")
        mirror = _json(self.runner, _truenas(("midclt", "call", "filesystem.listdir", "/mnt/Recovery/guests/aster-lxc110")), 10.0)
        verify_lxc110_mirror(mirror, artifacts[1])
        if verify_archives:
            for artifact in artifacts:
                code, path = self.runner(("pvesm", "path", artifact.volid), 10.0)
                if code != 0:
                    raise SourceAdapterError("backup path lookup failed")
                code, _ = self.runner(("zstd", "-t", "--quiet", path.strip()), 300.0)
                if code != 0:
                    raise SourceAdapterError("backup archive integrity check failed")
        receipt_material = json.dumps([(a.vmid, a.volid, a.size, a.ctime) for a in artifacts], separators=(",", ":"), sort_keys=True).encode()
        digest = hashlib.sha256(receipt_material).hexdigest()
        now = self.clock()
        return BackupSourceReceipt(EXPECTED_BACKUP_SOURCE, EXPECTED_BACKUP_SOURCE, now.hour * 60 + now.minute, f"metadata-sha256:{digest}", False, True)

    def _snapshot(self) -> ConsumerSnapshot:
        states, enters, masks = [], [], []
        for vmid, unit in PRODUCTION:
            code, output = self.runner(("pct", "exec", vmid, "--", "systemctl", "show", unit, "--property=ActiveState", "--property=ActiveEnterTimestampMonotonic", "--value"), 5.0)
            if code != 0:
                raise SourceAdapterError("consumer state probe failed")
            lines = output.splitlines()
            states.append(lines[0] if lines else "unknown")
            enters.append(int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else -1)
            code, mask = self.runner(("pct", "exec", vmid, "--", "readlink", "-f", f"/run/systemd/system/{unit}"), 5.0)
            if code != 0:
                raise SourceAdapterError("consumer mask probe failed")
            masks.append(mask.strip())
        code, news = self.runner(("pct", "exec", "114", "--", "systemctl", "is-active", "news-aggregator-digest.timer"), 5.0)
        if code not in (0, 3):
            raise SourceAdapterError("News timer probe failed")
        news_active = news.strip() == "active"
        return ConsumerSnapshot(self.clock().hour * 60 + self.clock().minute, self.monotonic(), tuple(states) + ("active" if news_active else "inactive",), tuple(enters) + (0,), news_active, "|".join(masks))

    def quiescence(self, *, interval_seconds: float = 10.0) -> QuiescenceSourceReceipt:
        first = self._snapshot()
        self.sleep(interval_seconds)
        try:
            return compose_quiescence_receipt(first, self._snapshot())
        except AdmissionEvidenceError as exc:
            raise SourceAdapterError(str(exc)) from exc

    def evidence(self, *, date_prefix: str, now_minute: int, window_end_minute: int):
        backup = self.backup(date_prefix=date_prefix)
        quiescence = self.quiescence()
        return compose_candidate_evidence(backup, quiescence, now_minute=now_minute, window_end_minute=window_end_minute)
