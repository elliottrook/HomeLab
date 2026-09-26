"""Controlled Aster payload-construction slice, never the production application.

Only explicitly selected local source definitions are compiled. No application
initialization, environment credentials, network adapters or model calls run.
This is a source-slice benchmark, not end-to-end latency or answer-quality evidence.
"""
from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import re
import time
from types import SimpleNamespace
from pathlib import Path
from typing import Any

from contracts import HarnessRun, Outcome

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'services/aster-agent/aster_agent.py'
ASSIGNMENTS = {'ASTER_SYSTEM_PROMPT', 'TOOLS', 'TOOL_HINTS'}
FUNCTIONS = {'select_tools', 'normalized_messages', 'preload_read_only_context', 'build_payload'}


def digest(data: bytes) -> str:
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def load_slice():
    source = SOURCE.read_bytes()
    parsed = ast.parse(source)
    selected, found = [], set()
    for node in parsed.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FUNCTIONS:
            selected.append(node)
            found.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = {t.id for t in targets if isinstance(t, ast.Name)}
            if names & ASSIGNMENTS:
                selected.append(node)
                found |= names & ASSIGNMENTS
    if found != ASSIGNMENTS | FUNCTIONS:
        raise ValueError('Aster source slice changed; review adapter compatibility')
    # Postponed annotations avoid importing FastAPI or initializing the app.
    module = ast.Module(body=[ast.ImportFrom(module='__future__',
                         names=[ast.alias(name='annotations')], level=0), *selected], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {'re': re, 'json': json, 'Any': Any,
                 'MAX_HEALTH_RESPONSE_TOKENS': 112, 'MAX_RESPONSE_TOKENS': 160,
                 'UPSTREAM_MODEL': 'fixture-no-model', 'DEFAULT_TIMEZONE': 'UTC',
                 'lab_operations': SimpleNamespace(enabled=set())}
    exec(compile(module, str(SOURCE), 'exec'), namespace)
    return namespace, digest(source)


class FixtureRequest:
    persona = 'fixture'
    stream = False

    def __init__(self, prompt: str):
        self.messages = [{'role': 'user', 'content': prompt}]

    def model_dump(self, **_):
        return {'messages': self.messages, 'max_tokens': 160, 'temperature': 0.0}


class FixtureExpired(Exception):
    pass


class FixtureAdapter:
    def __init__(self):
        self.namespace, self.source_digest = load_slice()

    async def run(self, contract: HarnessRun, prompt: str, *, now: int,
                  cancelled=lambda: False, monotonic=time.perf_counter) -> Outcome:
        # Revalidate even objects constructed with Pydantic's unchecked APIs.
        contract = HarnessRun.model_validate_json(contract.model_dump_json())
        if not isinstance(prompt, str) or len(prompt) > 512:
            raise ValueError('fixture prompt must be text up to 512 characters')
        started, calls, output_bytes = monotonic(), 0, 0

        def expired():
            return now + max(0, monotonic() - started) >= min(
                contract.decision.expires_at, contract.projection.expires_at)

        def outcome(status, verification='not-executed'):
            return Outcome(run_id=contract.run_id, status=status, verification=verification,
                           tool_calls=calls, elapsed_ms=float(max(0, (monotonic()-started)*1000)),
                           output_bytes=output_bytes)

        if contract.harness_digest != self.source_digest:
            return outcome('denied')
        if contract.decision.status not in {'plan', 'answer'}:
            return outcome('denied')
        if now >= min(contract.decision.expires_at, contract.projection.expires_at):
            return outcome('expired')
        if cancelled():
            return outcome('cancelled')
        by_id = {c.capability_id: c for c in contract.projection.capabilities}
        allowed = {by_id[s.capability_id].implementation for s in contract.decision.steps}
        # Functions have per-instance globals. Adapter instances must not run concurrently.
        async def fixture_execute(name, arguments):
            nonlocal calls
            if name not in allowed:
                raise PermissionError('unknown or denied fixture capability')
            if cancelled():
                raise asyncio.CancelledError()
            if expired():
                raise FixtureExpired()
            if calls >= contract.budget.tool_calls or (monotonic()-started)*1000 >= contract.budget.wall_ms:
                raise TimeoutError()
            calls += 1
            # Deliberately fixed, non-secret output. Arguments are transient and unrecorded.
            return {'fixture': True, 'status': 'available'}
        self.namespace['execute_tool'] = fixture_execute
        try:
            payload = await self.namespace['build_payload'](
                FixtureRequest(prompt), {'identity': 'Offline synthetic fixture'}, allowed)
            output_bytes = len(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode())
            if cancelled():
                return outcome('cancelled')
            if expired():
                return outcome('expired')
            if output_bytes > contract.budget.output_bytes or (monotonic()-started)*1000 >= contract.budget.wall_ms:
                return outcome('budget-exceeded')
            return outcome('completed', 'fixture-conformance')
        except asyncio.CancelledError:
            return outcome('cancelled')
        except FixtureExpired:
            return outcome('expired')
        except TimeoutError:
            return outcome('budget-exceeded')
        except PermissionError:
            return outcome('denied')
        except Exception:
            return outcome('failed')
