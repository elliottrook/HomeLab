import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from application_b60_lease import ACCEPTED_BACKEND
from full_inference_lab_sources import (AcceptedBaseline, FIXED, LOCAL_PROXMOX_FIXED,
    FullDrainSourceError, FullDrainSourceProducer, LocalProxmoxFullDrainSourceProducer,
    TrustedOwnerAttestation)


class FullInferenceLabSourcesTests(unittest.TestCase):
    def test_rejects_unattested_owner_before_host_probes(self):
        calls = []
        producer = FullDrainSourceProducer(lambda command, timeout: calls.append(command) or (0, ""),
            AcceptedBaseline("a" * 64, "b" * 64, "c" * 64), TrustedOwnerAttestation("", ""),
            wall_clock=lambda: 1000)
        with self.assertRaisesRegex(FullDrainSourceError, "attestation"):
            producer.collect(cycle="2026_10_18", session_start_epoch=1000)
        self.assertEqual(calls, [])

    def test_baseline_identity_is_explicit(self):
        baseline = AcceptedBaseline("a" * 64, "b" * 64, "c" * 64)
        self.assertEqual(ACCEPTED_BACKEND, "llama.cpp b11429 SYCL/Level Zero")
        self.assertEqual(len(baseline.model_sha256), 64)

    def test_next_timer_explicit_utc_is_converted_to_vancouver(self):
        producer = FullDrainSourceProducer(lambda command, timeout: (0, "Sun 2026-10-18 16:01:59 UTC  1h\n"),
            AcceptedBaseline("a" * 64, "b" * 64, "c" * 64), TrustedOwnerAttestation("owner-1", "m2"))
        expected = int(datetime(2026, 10, 18, 9, 1, 59, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        self.assertEqual(producer._next_ingest_epoch(expected - 60), expected)

    def test_collect_happy_path_uses_fixed_host_observations(self):
        now = int(datetime(2026, 10, 18, 10, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        finished = int(datetime(2026, 10, 18, 9, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp() * 1000)
        baseline = AcceptedBaseline("a" * 64, "b" * 64, "c" * 64)
        def runner(command, timeout):
            command = tuple(command)
            if command == FIXED["driver"]: return 0, "../../../../../../bus/pci/drivers/xe\n"
            if command == FIXED["vm"]: return 0, "status: stopped\n"
            if command == FIXED["vm_config"]: return 0, "memory: 1024\n"
            if command == FIXED["schedules"]: return 0, "[{\"vmid\":104,\"ctime\":%d,\"size\":10},{\"vmid\":110,\"ctime\":%d,\"size\":10},{\"vmid\":116,\"ctime\":%d,\"size\":10}]\n" % (finished // 1000, finished // 1000, finished // 1000)
            if command == FIXED["truenas"]:
                return 0, ("[{\"id\":1,\"enabled\":true,\"schedule\":{\"hour\":1,\"minute\":0},\"job\":{\"state\":\"SUCCESS\",\"arguments\":[1],\"time_started\":{\"$date\":%d},\"time_finished\":{\"$date\":%d}}},"
                           "{\"id\":2,\"enabled\":true,\"schedule\":{\"hour\":3,\"minute\":0},\"job\":{\"state\":\"SUCCESS\",\"arguments\":[2],\"time_started\":{\"$date\":%d},\"time_finished\":{\"$date\":%d}}},"
                           "{\"id\":3,\"enabled\":true,\"schedule\":{\"hour\":2,\"minute\":0},\"job\":{\"state\":\"SUCCESS\",\"arguments\":[3],\"time_started\":{\"$date\":%d},\"time_finished\":{\"$date\":%d}}}]\n" % (finished, finished, finished + 1, finished + 2, finished + 3, finished + 4))
            if command == FIXED["next_ingest"]: return 0, "Sun 2026-10-18 11:30:00 PDT  1h\n"
            if command in (FIXED["news_ingest_active"], FIXED["news_digest_active"]): return 0, "active\n"
            if command in (FIXED["news_ingest_enabled"], FIXED["news_digest_enabled"]): return 0, "enabled\n"
            if command == FIXED["gpu"]: return 0, ""
            if command == FIXED["auth"]: return 0, ""
            if command == FIXED["legacy_status"]: return 0, "ready\n"
            if command[-3:] in (("systemctl", "is-active", "aster-agent.service"),
                                ("systemctl", "is-active", "aster-llama.service"),
                                ("systemctl", "is-active", "aster-speech.service")): return 0, "active\n"
            if command[-2:] == ("sha256sum", "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"): return 0, "a" * 64 + " model\n"
            if command[-2:] == ("sha256sum", "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"): return 0, "b" * 64 + " binary\n"
            if command[-2:] == ("sha256sum", "/etc/systemd/system/aster-llama.service"): return 0, "c" * 64 + " unit\n"
            return 1, ""
        value = FullDrainSourceProducer(runner, baseline, TrustedOwnerAttestation("owner-1", "macbook-ssh-m2"),
                                        wall_clock=lambda: now).collect(cycle="2026_10_18", session_start_epoch=now)
        self.assertEqual(value.backend_identity, ACCEPTED_BACKEND)
        self.assertEqual(value.next_news_ingest_epoch, int(datetime(2026, 10, 18, 11, 30, tzinfo=ZoneInfo("America/Vancouver")).timestamp()))

    def test_collect_rejects_stale_or_missing_backup_task(self):
        baseline = AcceptedBaseline("a" * 64, "b" * 64, "c" * 64)
        def runner(command, timeout):
            if tuple(command) == FIXED["driver"]: return 0, "../../../../../../bus/pci/drivers/xe\n"
            if tuple(command) == FIXED["vm"]: return 0, "status: stopped\n"
            if tuple(command) == FIXED["vm_config"]: return 0, "memory: 1024\n"
            if tuple(command) == FIXED["schedules"]: return 0, "[{\"vmid\":104,\"ctime\":1792320000,\"size\":10}]\n"
            if tuple(command) == FIXED["truenas"]: return 0, "[{\"id\":1,\"enabled\":true,\"job\":{\"state\":\"SUCCESS\"}}]\n"
            if tuple(command[-2:]) == ("sha256sum", "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"): return 0, "a" * 64 + " model\n"
            if tuple(command[-2:]) == ("sha256sum", "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"): return 0, "b" * 64 + " binary\n"
            if tuple(command[-2:]) == ("sha256sum", "/etc/systemd/system/aster-llama.service"): return 0, "c" * 64 + " unit\n"
            return 0, ""
        producer = FullDrainSourceProducer(runner, baseline, TrustedOwnerAttestation("owner-1", "macbook-ssh-m2"),
                                           wall_clock=lambda: 1792336800)
        with self.assertRaisesRegex(FullDrainSourceError, "backup"):
            producer.collect(cycle="2026_10_18", session_start_epoch=1792336800)

    def test_local_proxmox_mode_proves_cycle_and_never_calls_truenas(self):
        now = int(datetime(2026, 10, 18, 10, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        artifact = int(datetime(2026, 10, 18, 0, 34, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        started = int(datetime(2026, 10, 18, 0, 30, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        finished = int(datetime(2026, 10, 18, 0, 35, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        calls = []
        def runner(command, timeout):
            command = tuple(command)
            calls.append(command)
            if command == FIXED["schedules"]:
                return 0, "[{\"vmid\":104,\"ctime\":%d,\"size\":10},{\"vmid\":110,\"ctime\":%d,\"size\":10},{\"vmid\":116,\"ctime\":%d,\"size\":10}]" % (artifact, artifact, artifact)
            if command == LOCAL_PROXMOX_FIXED["backup_job"]:
                return 0, "{\"id\":\"backup-49999802-1365\",\"enabled\":1,\"schedule\":\"00:30\",\"storage\":\"backups\",\"type\":\"vzdump\",\"all\":1}"
            if command == LOCAL_PROXMOX_FIXED["backup_tasks"]:
                return 0, json.dumps([{"upid": "UPID:proxmox:ABC:DEF:123:vzdump::root@pam", "type": "vzdump", "status": "OK", "starttime": started, "endtime": finished, "node": "proxmox"}])
            if command == FIXED["truenas"]:
                raise AssertionError("local-only pilot must not call TrueNAS")
            return 1, ""
        producer = LocalProxmoxFullDrainSourceProducer(
            runner, AcceptedBaseline("a" * 64, "b" * 64, "c" * 64),
            TrustedOwnerAttestation("owner-1", "macbook-ssh-m2"), wall_clock=lambda: now)
        self.assertTrue(producer._backup_current("2026_10_18"))
        self.assertNotIn(FIXED["truenas"], calls)

    def test_local_proxmox_mode_rejects_missing_whole_job_completion(self):
        now = int(datetime(2026, 10, 18, 10, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        artifact = int(datetime(2026, 10, 18, 9, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        def runner(command, timeout):
            command = tuple(command)
            if command == FIXED["schedules"]:
                return 0, "[{\"vmid\":104,\"ctime\":%d,\"size\":10},{\"vmid\":110,\"ctime\":%d,\"size\":10},{\"vmid\":116,\"ctime\":%d,\"size\":10}]" % (artifact, artifact, artifact)
            if command == LOCAL_PROXMOX_FIXED["backup_job"]:
                return 0, "{\"id\":\"backup-49999802-1365\",\"enabled\":1,\"schedule\":\"00:30\",\"storage\":\"backups\",\"type\":\"vzdump\",\"all\":1}"
            return 0, ""
        producer = LocalProxmoxFullDrainSourceProducer(
            runner, AcceptedBaseline("a" * 64, "b" * 64, "c" * 64),
            TrustedOwnerAttestation("owner-1", "macbook-ssh-m2"), wall_clock=lambda: now)
        self.assertFalse(producer._backup_current("2026_10_18"))


if __name__ == "__main__":
    unittest.main()
