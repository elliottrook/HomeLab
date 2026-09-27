"""Fixed synthetic M2 corpus; no private data or production authority mapping."""
import hashlib
import json

from contracts import Budget, Capability, Decision, HarnessRun, Step, project_catalogue

def content_digest(value):
    return 'sha256:' + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


POLICY = content_digest({'version': 1, 'scope': 'fixture-only', 'grant_rule': 'explicit-permission-reference'})
INPUT_SCHEMA = {'type': 'object', 'additionalProperties': True}
OUTPUT_SCHEMA = {'type': 'object', 'additionalProperties': False,
                 'properties': {'fixture': {'const': True}, 'status': {'const': 'available'}},
                 'required': ['fixture', 'status']}
CATALOGUE = tuple(Capability(capability_id='fixture.' + name, implementation=tool,
                            owner='fixture-owner', permission_ref='fixture.' + name,
                            input_schema=content_digest(INPUT_SCHEMA), output_schema=content_digest(OUTPUT_SCHEMA))
                  for name, tool in [('time', 'get_current_time'), ('ha', 'get_ha_report'),
                                     ('forgejo', 'get_forgejo_report'), ('netbox', 'get_netbox_report')])
REGISTRY = content_digest([c.model_dump(mode='json') for c in CATALOGUE])
CASES = (
    ('no-tool', 'Tell me a short joke', ()),
    ('one-read', 'What time is it?', ('fixture.time',)),
    ('two-reads', 'Show current Forgejo and NetBox inventory status', ('fixture.forgejo', 'fixture.netbox')),
    ('ha-read', 'What is the current Home Assistant version?', ('fixture.ha',)),
)


def make_run(source_digest, ids=('fixture.time',)):
    projection = project_catalogue(CATALOGUE, granted=frozenset(ids), principal_ref='fixture-user',
                                   policy_digest=POLICY, registry_digest=REGISTRY, expires_at=1300)
    decision = Decision(request_id='fixture-request', principal_ref='fixture-user',
                        status='plan' if ids else 'answer', reason='supported',
                        steps=tuple(Step(step_id=f's{i}', capability_id=cap) for i, cap in enumerate(ids)),
                        expires_at=1200, policy_digest=POLICY, registry_digest=REGISTRY)
    return HarnessRun(run_id='fixture-run', experiment_id='m2-baseline', principal_ref='fixture-user',
                      projection=projection, decision=decision,
                      budget=Budget(wall_ms=1000, tool_calls=len(ids), output_bytes=65536),
                      harness_digest=source_digest)
