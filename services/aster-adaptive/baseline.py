"""Extract the trusted repository's pure selector without importing the application.

This is an offline benchmark adapter, never an execution or authorization path.
The source digest is pinned by the caller and retained in every result.
"""
from __future__ import annotations
import ast
import hashlib
import re
import time
from pathlib import Path
from contracts import Catalogue, Decision, DecisionRequest, Step


class BaselineSelector:
    def __init__(self, source: Path, expected_digest: str):
        raw = source.read_bytes()
        self.digest = hashlib.sha256(raw).hexdigest()
        if self.digest != expected_digest:
            raise ValueError('baseline source changed')
        tree = ast.parse(raw)
        hints = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TOOL_HINTS' for t in n.targets)]
        selectors = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'select_tools']
        if len(hints) != 1 or len(selectors) != 1:
            raise ValueError('unsupported baseline layout')
        values = hints[0].value
        if not isinstance(values, ast.Dict):
            raise ValueError('unsupported hints')
        patterns = {}
        for key, value in zip(values.keys, values.values):
            name = ast.literal_eval(key)
            if not isinstance(name, str) or not isinstance(value, ast.Call) or ast.unparse(value.func) != 're.compile' or len(value.args) != 2 or value.keywords or ast.unparse(value.args[1]) != 're.I':
                raise ValueError('unsupported regex declaration')
            patterns[name] = re.compile(ast.literal_eval(value.args[0]), re.I)
        # This reviewed, digest-pinned function alone is compiled. No app/module
        # initialization, imports, endpoints or tool implementations are executed.
        module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), selectors[0]], type_ignores=[])
        namespace = {'TOOL_HINTS': patterns, 'TOOLS': {n: {'function': {'name': n}} for n in patterns}}
        exec(compile(ast.fix_missing_locations(module), str(source), 'exec'), namespace)
        self.select = namespace['select_tools']
        self.names = frozenset(patterns)

    def propose(self, request: DecisionRequest, catalogue: Catalogue, messages: list[dict], *, now: int) -> Decision:
        if len(messages) > 32 or any(not isinstance(m, dict) or set(m) - {'role', 'content'} or m.get('role') not in {'user', 'system', 'assistant', 'tool'} or not isinstance(m.get('content'), str) or len(m['content']) > 4096 for m in messages):
            raise ValueError('unsupported or oversized synthetic messages')
        started = time.monotonic_ns()
        if request.registry_digest != catalogue.digest() or catalogue.source_digest != self.digest or request.engine_digest != self.digest:
            status, reason, names = 'deny', 'STALE_REGISTRY', []
        else:
            known = {c.capability_id for c in catalogue.capabilities}
            all_names = [t['function']['name'] for t in self.select(messages)]
            names = [name for name in all_names if name in known]
            if not known <= self.names:
                status, reason, names = 'deny', 'UNKNOWN_CAPABILITY', []
            elif all_names and not names:
                status, reason, names = 'deny', 'FIXTURE_POLICY_DENY', []
            elif len(names) > request.max_steps:
                status, reason, names = 'abstain', 'STEP_BUDGET_EXCEEDED', []
            else:
                status, reason = ('plan', 'BASELINE_TOOL_MATCH') if names else ('abstain', 'NO_BASELINE_TOOL')
        if time.monotonic_ns() - started > request.deadline_ms * 1_000_000:
            status, reason, names = 'degraded', 'DEADLINE_EXCEEDED', []
        return Decision(request_id=request.request_id, registry_digest=request.registry_digest,
                        policy_digest=request.policy_digest, engine_digest=self.digest,
                        status=status, reason_codes=[reason],
                        steps=[Step(step_id=f'step-{i}', capability_id=name) for i, name in enumerate(names)],
                        expires_unix=now + 30)
