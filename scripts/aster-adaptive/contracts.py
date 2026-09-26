"""Versioned offline foundation contracts. These objects never grant authority."""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Ref = Annotated[str, Field(pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$')]
Digest = Annotated[str, Field(pattern=r'^sha256:[a-f0-9]{64}$')]
Tool = Literal['get_current_time', 'get_ha_report', 'get_forgejo_report', 'get_netbox_report']


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


class Capability(Contract):
    schema_version: Literal['capability.v1'] = 'capability.v1'
    capability_id: Ref
    implementation: Tool
    owner: Ref
    permission_ref: Ref
    input_schema: Digest
    output_schema: Digest
    locality: Literal['fixture-only'] = 'fixture-only'
    effects: Literal['none'] = 'none'


class Projection(Contract):
    schema_version: Literal['projection.v1'] = 'projection.v1'
    principal_ref: Ref
    policy_digest: Digest
    registry_digest: Digest
    expires_at: Annotated[int, Field(ge=1)]
    capabilities: tuple[Capability, ...]
    authority: Literal['not-granted'] = 'not-granted'

    @model_validator(mode='after')
    def unique(self):
        ids = [c.capability_id for c in self.capabilities]
        tools = [c.implementation for c in self.capabilities]
        if len(ids) != len(set(ids)) or len(tools) != len(set(tools)):
            raise ValueError('duplicate capability or implementation')
        return self


class Step(Contract):
    step_id: Ref
    capability_id: Ref
    after: tuple[Ref, ...] = ()


class Decision(Contract):
    schema_version: Literal['decision.v1'] = 'decision.v1'
    request_id: Ref
    principal_ref: Ref
    status: Literal['plan', 'answer', 'clarify', 'abstain', 'unsupported', 'deny']
    steps: Annotated[tuple[Step, ...], Field(max_length=8)] = ()
    reason: Literal['supported', 'ambiguous', 'unavailable', 'policy-denied']
    expires_at: Annotated[int, Field(ge=1)]
    policy_digest: Digest
    registry_digest: Digest
    confidence: None = None  # No calibrated probabilities are available in M2.
    authorization: Literal['not-granted'] = 'not-granted'

    @model_validator(mode='after')
    def ordered_dag(self):
        if (self.status == 'plan') != bool(self.steps):
            raise ValueError('only plans contain nonempty steps')
        seen = set()
        for step in self.steps:
            if step.step_id in seen or not set(step.after) <= seen:
                raise ValueError('steps must form a uniquely named topologically ordered DAG')
            if len(set(step.after)) != len(step.after):
                raise ValueError('duplicate dependency')
            seen.add(step.step_id)
        return self


class Budget(Contract):
    wall_ms: Annotated[int, Field(ge=1, le=10000)]
    model_calls: Literal[0] = 0
    tool_calls: Annotated[int, Field(ge=0, le=8)]
    output_bytes: Annotated[int, Field(ge=1, le=65536)]


class HarnessRun(Contract):
    schema_version: Literal['run.v1'] = 'run.v1'
    run_id: Ref
    experiment_id: Ref
    principal_ref: Ref
    decision: Decision
    projection: Projection
    budget: Budget
    harness_digest: Digest
    data_class: Literal['synthetic'] = 'synthetic'

    @model_validator(mode='after')
    def bind(self):
        d, p = self.decision, self.projection
        if self.principal_ref != d.principal_ref or d.principal_ref != p.principal_ref:
            raise ValueError('principal mismatch')
        if (d.policy_digest, d.registry_digest) != (p.policy_digest, p.registry_digest):
            raise ValueError('stale policy or registry')
        eligible = {c.capability_id for c in p.capabilities}
        if any(s.capability_id not in eligible for s in d.steps):
            raise ValueError('unknown or unprojected capability')
        if d.expires_at > p.expires_at:
            raise ValueError('decision outlives projection')
        if len(d.steps) > self.budget.tool_calls:
            raise ValueError('plan exceeds tool budget')
        return self


class Outcome(Contract):
    schema_version: Literal['outcome.v1'] = 'outcome.v1'
    run_id: Ref
    status: Literal['completed', 'denied', 'expired', 'cancelled', 'budget-exceeded', 'failed']
    verification: Literal['fixture-conformance', 'not-executed']
    tool_calls: Annotated[int, Field(ge=0, le=8)]
    model_calls: Literal[0] = 0
    elapsed_ms: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    output_bytes: Annotated[int, Field(ge=0)]
    prompt_tokens: None = None
    quality: Literal['not-evaluated'] = 'not-evaluated'
    data_class: Literal['synthetic'] = 'synthetic'


class Experiment(Contract):
    schema_version: Literal['experiment.v1'] = 'experiment.v1'
    experiment_id: Ref
    owner: Ref
    baseline_digest: Digest
    candidate_digest: Digest
    evaluator_digest: Digest
    dataset_digest: Digest
    status: Literal['preregistered', 'measured', 'retain', 'reject']
    metric: Literal['offline-payload-construction-ms']
    interpretation: Literal['controlled-overhead-only'] = 'controlled-overhead-only'
    promotion_authority: Literal['none'] = 'none'
    data_class: Literal['synthetic'] = 'synthetic'


def project_catalogue(catalogue: tuple[Capability, ...], *, granted: frozenset[str],
                      principal_ref: str, policy_digest: str, registry_digest: str,
                      expires_at: int) -> Projection:
    """Trusted fixture-policy input only. Production must use broker-owned grants."""
    # Validate the complete catalogue before filtering, so collisions cannot hide.
    all_items = Projection(principal_ref=principal_ref, policy_digest=policy_digest,
                           registry_digest=registry_digest, expires_at=expires_at,
                           capabilities=catalogue)
    return Projection(principal_ref=principal_ref, policy_digest=policy_digest,
                      registry_digest=registry_digest, expires_at=expires_at,
                      capabilities=tuple(c for c in all_items.capabilities
                                         if c.permission_ref in granted))
