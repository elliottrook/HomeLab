"""Offline process-contract proof; all host/process boundaries are fake."""
import ast
import json
import subprocess
import types
import unittest
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo


class ScheduledError(Exception):
    pass


class SubcheckError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class GuardError(Exception):
    pass


def isolated_final(correct_default=False):
    source = Path(__file__).with_name("final_fixture.py").read_text()
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    if correct_default:
        function.args.kw_defaults[0] = ast.Attribute(
            value=ast.Name(id="subprocess", ctx=ast.Load()),
            attr="Popen", ctx=ast.Load(),
        )
    events = []
    failures = []
    writes = []
    epoch = datetime(2026, 10, 26, 1, 20, tzinfo=ZoneInfo("America/Vancouver")).timestamp()

    def completed_process(*args, **kwargs):
        events.append("run")
        # Match subprocess.run's returned interface; launch nothing.
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=b"{}")

    def process_handle(*args, **kwargs):
        events.append("Popen")
        assert kwargs["start_new_session"] is True
        assert "secret" not in str(kwargs)
        return types.SimpleNamespace(
            pid=123, returncode=0,
            communicate=lambda timeout: (b'{"synthetic":true}', None),
        )

    fake_subprocess = types.SimpleNamespace(
        run=completed_process, Popen=process_handle, PIPE=-1, DEVNULL=-3,
        TimeoutExpired=subprocess.TimeoutExpired,
    )
    schema = "aster-f2-scheduled.v1"
    namespace = {
        "Callable": Callable,
        "subprocess": fake_subprocess,
        "time": types.SimpleNamespace(time=lambda: epoch),
        "datetime": datetime,
        "LOCAL_ZONE": ZoneInfo("America/Vancouver"),
        "FINAL_MINUTE": 80,
        "SCHEMA": schema,
        "ScheduledF2Error": ScheduledError,
        "FinalSubcheckError": SubcheckError,
        "F2FinalGuardError": GuardError,
        "_cycle": lambda value: ("2026-10-26", 80),
        "_existing_state": lambda cycle: {
            "schema": schema, "cycle": cycle, "phase": "prepare",
            "state": "prepared", "error_class": "",
            "first_failure_phase": "", "failure_class": "",
        },
        "run_fixed_final_guard": lambda runner: None,
        "OBSERVER": Path("/synthetic/not-executed/observer.py"),
        "json": json,
        "_validate_projection": lambda value, cycle: None,
        "_write_state": lambda *args, **kwargs: writes.append((args, kwargs)),
        "_record_failure": lambda cycle, phase, error: failures.append(error),
    }
    # There is no OS/network implementation in the function's globals.
    exec(compile(ast.fix_missing_locations(tree), "<isolated-final>", "exec"), namespace)
    return namespace["final"], events, failures, writes


class DefaultProcessContractTests(unittest.TestCase):
    def test_installed_default_reproduces_communication_failure(self):
        final, events, failures, writes = isolated_final()
        with self.assertRaises(SubcheckError) as raised:
            final(lambda *args: (0, "synthetic"))
        self.assertEqual("OBSERVER_COMMUNICATION_FAILED", raised.exception.code)
        self.assertIsInstance(raised.exception.__cause__, AttributeError)
        self.assertEqual(["run"], events)
        self.assertEqual([raised.exception], failures)
        self.assertEqual([], writes)

    def test_one_default_change_accepts_the_expected_process_handle(self):
        final, events, failures, writes = isolated_final(correct_default=True)
        result = final(lambda *args: (0, "synthetic"))
        self.assertEqual("complete", result["state"])
        self.assertEqual({"synthetic": True}, result["result"])
        self.assertEqual(["Popen"], events)
        self.assertEqual([], failures)
        self.assertEqual(1, len(writes))


if __name__ == "__main__":
    unittest.main()
