"""Extract the trusted repository's pure selector without importing the application.

This is an offline benchmark adapter, never an execution or authorization path.
The source digest is pinned by the caller and retained in every result.
"""
from __future__ import annotations
import ast
import hashlib
import re
import symtable
import time
from pathlib import Path
from contracts import Catalogue, Decision, DecisionRequest, Step

COMPONENT_NAMES = frozenset({'TOOLS', 'TOOL_HINTS', 'select_tools'})


def component_digests(raw: bytes) -> dict[str, str]:
    """Pin exactly the selector and declarations this offline adapter consumes."""
    source = raw.decode('utf-8')
    tree = ast.parse(raw)
    found = {}
    for node in tree.body:
        names = []
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = [node.name]
        for name in names:
            if name in COMPONENT_NAMES:
                if name in found:
                    raise ValueError('duplicate baseline component')
                found[name] = node
    if set(found) != COMPONENT_NAMES:
        raise ValueError('missing baseline component')
    segments = {name: ast.get_source_segment(source, found[name]) for name in COMPONENT_NAMES}
    if any(segment is None for segment in segments.values()):
        raise ValueError('baseline component source is unavailable')
    return {name: hashlib.sha256(segments[name].encode()).hexdigest()
            for name in sorted(COMPONENT_NAMES)}


class BaselineSelector:
    def __init__(self, source: Path, expected_digest: str | None = None, *,
                 expected_components: dict[str, str] | None = None):
        if (expected_digest is None) == (expected_components is None):
            raise ValueError('exactly one reviewed source pin is required')
        raw = source.read_bytes()
        self.digest = hashlib.sha256(raw).hexdigest()
        if expected_digest is not None and self.digest != expected_digest:
            raise ValueError('baseline source changed')
        self.component_digests = component_digests(raw)
        if expected_components is not None and (
            set(expected_components) != COMPONENT_NAMES or
            any(not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value)
                for value in expected_components.values()) or
            self.component_digests != expected_components
        ):
            raise ValueError('baseline selector component changed')
        tree = ast.parse(raw)
        hints = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TOOL_HINTS' for t in n.targets)]
        selectors = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'select_tools']
        if len(hints) != 1 or len(selectors) != 1:
            raise ValueError('unsupported baseline layout')
        selector_source = ast.get_source_segment(raw.decode('utf-8'), selectors[0])
        if selector_source is None:
            raise ValueError('baseline selector source is unavailable')
        symbols = symtable.symtable('from __future__ import annotations\n' + selector_source,
                                   str(source), 'exec')
        globals_used = set()
        def collect_globals(table):
            for child in table.get_children():
                globals_used.update(symbol.get_name() for symbol in child.get_symbols()
                                    if symbol.is_global())
                collect_globals(child)
        collect_globals(symbols)
        if globals_used != {'TOOLS', 'TOOL_HINTS', 'str'}:
            raise ValueError('baseline selector has unreviewed global dependencies')
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
            elif len(names) != len(all_names):
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
