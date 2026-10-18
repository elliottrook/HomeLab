import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from full_inference_lab_sources import AcceptedBaseline, FIXED
from full_inference_lab_validator import FullDrainValidator


class FullInferenceValidatorTests(unittest.TestCase):
    def test_validates_accepted_baseline_and_runtime(self):
        baseline = AcceptedBaseline("a" * 64, "b" * 64, "c" * 64)
        now = int(datetime(2026, 10, 18, 10, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        started = int(datetime(2026, 10, 18, 7, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp() * 1000)
        finished = int(datetime(2026, 10, 18, 9, 0, tzinfo=ZoneInfo("America/Vancouver")).timestamp() * 1000)
        def runner(command, timeout):
            command = tuple(command)
            if command == FIXED["driver"]:
                return 0, "/sys/bus/pci/drivers/xe\n"
            if command == FIXED["vm"]:
                return 0, "status: stopped\n"
            if command == FIXED["vm_config"]:
                return 0, "memory: 1024\n"
            if command == FIXED["schedules"]:
                return 0, "[{\"vmid\":104,\"ctime\":%d,\"size\":10},{\"vmid\":110,\"ctime\":%d,\"size\":10},{\"vmid\":116,\"ctime\":%d,\"size\":10}]\n" % (started // 1000, started // 1000, started // 1000)
            if command == FIXED["truenas"]:
                return 0, ("[{\"id\":1,\"enabled\":true,\"schedule\":{\"hour\":1,\"minute\":0},\"job\":{\"state\":\"SUCCESS\",\"arguments\":[1],\"time_started\":{\"$date\":%d},\"time_finished\":{\"$date\":%d}}}," % (started, finished)
                           + "{\"id\":3,\"enabled\":true,\"schedule\":{\"hour\":2,\"minute\":0},\"job\":{\"state\":\"SUCCESS\",\"arguments\":[3],\"time_started\":{\"$date\":%d},\"time_finished\":{\"$date\":%d}}}," % (finished + 1, finished + 2)
                           + "{\"id\":2,\"enabled\":true,\"schedule\":{\"hour\":3,\"minute\":0},\"job\":{\"state\":\"SUCCESS\",\"arguments\":[2],\"time_started\":{\"$date\":%d},\"time_finished\":{\"$date\":%d}}}]\n" % (finished + 3, finished + 4))
            if command[-2:] == ("sha256sum", "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"):
                return 0, "a" * 64 + "  model\n"
            if command[-2:] == ("sha256sum", "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"):
                return 0, "b" * 64 + "  binary\n"
            if command[-2:] == ("sha256sum", "/etc/systemd/system/aster-llama.service"):
                return 0, "c" * 64 + "  unit\n"
            if command[-3:] == ("systemctl", "is-active", "aster-llama.service"):
                return 0, "active\n"
            if command[-3:] == ("systemctl", "is-active", "aster-speech.service"):
                return 0, "active\n"
            if command[-3:] == ("systemctl", "is-active", "aster-agent.service"):
                return 0, "active\n"
            if command == FIXED["news_ingest_active"] or command == FIXED["news_digest_active"]:
                return 0, "active\n"
            if command == FIXED["news_ingest_enabled"] or command == FIXED["news_digest_enabled"]:
                return 0, "enabled\n"
            if command == FIXED["auth"]:
                return 0, ""
            return 1, ""
        self.assertTrue(FullDrainValidator(runner, baseline, cycle="2026_10_18", wall_clock=lambda: now)())

    def test_hash_drift_fails_closed(self):
        self.assertFalse(FullDrainValidator(lambda command, timeout: (1, ""),
                                             AcceptedBaseline("a" * 64, "b" * 64, "c" * 64),
                                             cycle="2026_10_18")())


if __name__ == "__main__":
    unittest.main()
