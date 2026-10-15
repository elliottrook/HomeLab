import importlib.util
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("m3_compat", HERE / "m3_9b_sycl_compat.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class CompatTests(unittest.TestCase):
    def setUp(self):
        self.rows = probe.validate_fixture((HERE / "fixtures/routing-families-v1.json").read_bytes())

    def test_transport_embeds_only_pinned_fixture_and_compiles(self):
        result = subprocess.run([sys.executable, str(HERE / "build_m3_9b_transport.py")],
                                check=True, capture_output=True, text=True)
        compile(result.stdout, "transport", "exec")
        self.assertEqual(len(self.rows), 30)
        self.assertNotIn("ASTER_LLAMA_API_KEY", result.stdout)

    def test_v4_prompt_states_nonplan_capability_rule(self):
        self.assertIn("capabilities MUST be an empty array", probe.SYSTEM)
        self.assertIn("m3-9b-sycl-compat.v4", probe.run([], "synthetic-secret")["schema"])

    def test_mocked_complete_run_excludes_key_and_request_text(self):
        iterator = iter(self.rows)

        def fake(request, timeout):
            row = next(iterator)
            self.assertEqual(timeout, 90)
            self.assertEqual(request.get_header("Authorization"), "Bearer synthetic-secret")
            value = {"choices": [{"message": {"content": json.dumps({
                "status": row["status"], "capabilities": row["required"]})}}]}
            return Reply(json.dumps(value).encode())

        result = probe.run(self.rows, "synthetic-secret", request_fn=fake)
        self.assertEqual(result["attempted"], 30)
        self.assertEqual(result["valid"], 30)
        self.assertEqual(result["exact_match"], 30)
        serialized = json.dumps(result)
        self.assertNotIn("synthetic-secret", serialized)
        self.assertNotIn(self.rows[0]["text"], serialized)
        self.assertIn("p95_seconds", result)

    def test_complete_run_uses_nearest_rank_p95(self):
        ticks = [0]
        elapsed = 0
        for latency in range(1, 31):
            ticks.extend((elapsed, elapsed, elapsed + latency))
            elapsed += latency
        ticks.append(elapsed)
        clock = iter(ticks)
        iterator = iter(self.rows)

        def fake(_request, timeout):
            row = next(iterator)
            return Reply(json.dumps({"choices": [{"message": {"content": json.dumps({
                "status": row["status"], "capabilities": row["required"]})}}]}).encode())

        result = probe.run(self.rows, "synthetic-secret", request_fn=fake,
                           now=lambda: next(clock))
        self.assertEqual(result["p95_seconds"], 29)

    def test_first_invalid_response_stops_without_retry(self):
        calls = 0

        def bad(_request, timeout):
            nonlocal calls
            calls += 1
            return Reply(b'{"choices":[{"message":{"content":"not JSON"}}]}')

        result = probe.run(self.rows, "synthetic-secret", request_fn=bad)
        self.assertEqual(calls, 1)
        self.assertEqual(result["attempted"], 1)
        self.assertEqual(result["records"][0]["failure"], "invalid_response")
        self.assertNotIn("p95_seconds", result)

    def test_http_error_records_status_without_body(self):
        def bad(_request, timeout):
            raise HTTPError(probe.ENDPOINT, 401, "synthetic-secret", {}, io.BytesIO(b"private"))

        result = probe.run(self.rows, "synthetic-secret", request_fn=bad)
        self.assertEqual(result["records"][0]["http_status"], 401)
        self.assertNotIn("synthetic-secret", json.dumps(result))
        self.assertNotIn("private", json.dumps(result))

    def test_unknown_capability_and_extra_fields_are_rejected(self):
        for content in [
            '{"status":"plan","capabilities":["shell"]}',
            '{"status":"clarify","capabilities":["calendar"]}',
            '{"status":"plan","capabilities":[],"explanation":"hidden"}',
        ]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                probe.parse_response({"choices": [{"message": {"content": content}}]})

    def test_diagnostic_reports_parse_stage_without_content_or_key(self):
        def fake(_request, timeout):
            value = {"choices": [{"finish_reason": "stop", "message": {
                "content": "synthetic-private-marker-not-json"}}]}
            return Reply(json.dumps(value).encode())

        result = probe.diagnose_one(self.rows[1], "synthetic-secret", request_fn=fake)
        self.assertEqual(result["stage"], "json_syntax")
        self.assertEqual(result["finish_reason"], "stop")
        text = json.dumps(result)
        self.assertNotIn("synthetic-private-marker", text)
        self.assertNotIn("synthetic-secret", text)
        self.assertNotIn(self.rows[1]["text"], text)

    def test_diagnostic_distinguishes_valid_json_wrong_shape(self):
        def fake(_request, timeout):
            value = {"choices": [{"finish_reason": "length", "message": {
                "content": '{"status":"plan","capabilities":[],"why":"synthetic"}'}}]}
            return Reply(json.dumps(value).encode())

        result = probe.diagnose_one(self.rows[1], "synthetic-secret", request_fn=fake)
        self.assertEqual(result["stage"], "schema_or_capability")
        self.assertEqual(result["extra_key_count"], 1)
        self.assertEqual(result["finish_reason"], "length")
        self.assertNotIn("synthetic", json.dumps(result))

    def test_diagnostic_value_flags_do_not_echo_unknown_values(self):
        def fake(_request, timeout):
            value = {"choices": [{"finish_reason": "stop", "message": {
                "content": '{"status":"private-status","capabilities":["timer","private-capability"]}'}}]}
            return Reply(json.dumps(value).encode())

        result = probe.diagnose_one(self.rows[2], "synthetic-secret", request_fn=fake)
        self.assertEqual(result["stage"], "schema_or_capability")
        self.assertFalse(result["status_allowed"])
        self.assertEqual(result["unknown_capability_count"], 1)
        self.assertNotIn("private-status", json.dumps(result))
        self.assertNotIn("private-capability", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
