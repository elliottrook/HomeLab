"""Offline v1 contract candidate. No model, network, credential or execution client."""
from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_.-]{0,95}$')]
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Nonnegative = Annotated[int, Field(ge=0)]


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


class Capability(Contract):
    schema_version: Literal['capability.v1'] = 'capability.v1'
    capability_id: Identifier
    implementation: Identifier
    input_schema_digest: Digest
    output_schema_digest: Digest
    effect: Literal['read', 'proposal']
    locality: Literal['local'] = 'local'
    sensitivity: Literal['public', 'internal', 'personal']
    owner: Literal['jason'] = 'jason'
    execution: Literal['disabled'] = 'disabled'


class Catalogue(Contract):
    schema_version: Literal['catalogue.v1'] = 'catalogue.v1'
    source_digest: Digest
    capabilities: Annotated[list[Capability], Field(max_length=32)]
    scope: Literal['offline-fixture-not-permission'] = 'offline-fixture-not-permission'

    @model_validator(mode='after')
    def unique(self):
        ids = [c.capability_id for c in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate capability')
        return self

    def digest(self):
        return hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class DecisionRequest(Contract):
    schema_version: Literal['decision-request.v1'] = 'decision-request.v1'
    request_id: Identifier
    content_handle: Identifier  # no prompt or arbitrary URL; fixture key only
    registry_digest: Digest
    policy_digest: Digest
    sensitivity: Literal['public', 'internal', 'personal']
    egress: Literal['none'] = 'none'
    deadline_ms: Annotated[int, Field(ge=1, le=5000)]
    max_steps: Annotated[int, Field(ge=1, le=8)] = 8
    retention: Literal['synthetic-only'] = 'synthetic-only'


class Step(Contract):
    step_id: Identifier
    capability_id: Identifier
    after: Annotated[list[Identifier], Field(max_length=8)] = Field(default_factory=list)


class Decision(Contract):
    schema_version: Literal['decision.v1'] = 'decision.v1'
    request_id: Identifier
    registry_digest: Digest
    policy_digest: Digest
    engine_digest: Digest
    status: Literal['plan', 'abstain', 'deny', 'degraded', 'unsupported', 'clarify']
    steps: Annotated[list[Step], Field(max_length=8)] = Field(default_factory=list)
    reason_codes: Annotated[list[Literal['BASELINE_TOOL_MATCH', 'NO_BASELINE_TOOL', 'UNKNOWN_CAPABILITY', 'STALE_REGISTRY', 'DEADLINE_EXCEEDED', 'FIXTURE_POLICY_DENY', 'STEP_BUDGET_EXCEEDED']], Field(min_length=1, max_length=8)]
    probability: None = None  # uncalibrated baseline has no probability claim
    authorization: Literal['not_granted'] = 'not_granted'
    expires_unix: Annotated[int, Field(gt=0)]

    @model_validator(mode='after')
    def graph(self):
        if (self.status == 'plan') != bool(self.steps):
            raise ValueError('only plans have nonempty steps')
        seen = set()
        for step in self.steps:
            if step.step_id in seen or len(step.after) != len(set(step.after)):
                raise ValueError('duplicate step or dependency')
            if not set(step.after) <= seen:
                raise ValueError('dependencies must reference earlier steps')
            seen.add(step.step_id)
        return self


class HarnessRun(Contract):
    schema_version: Literal['harness-run.v1'] = 'harness-run.v1'
    run_id: Identifier
    request_id: Identifier
    decision_digest: Digest
    adapter_digest: Digest
    mode: Literal['offline-selection-only'] = 'offline-selection-only'
    duration_ns: Nonnegative
    model_calls: Literal[0] = 0
    tool_calls: Literal[0] = 0
    external_cost_usd: Literal[0] = 0
    execution: Literal['not_attempted'] = 'not_attempted'


class Outcome(Contract):
    schema_version: Literal['outcome.v1'] = 'outcome.v1'
    run_id: Identifier
    result: Literal['selection_recorded', 'abstained', 'denied', 'invalid']
    execution: Literal['not_attempted'] = 'not_attempted'
    label_source: Literal['synthetic_expectation', 'unlabeled']
    route_correct: bool | None
    # No free text, raw content, tool arguments/results, principal, token or reasoning.


class Experiment(Contract):
    schema_version: Literal['experiment.v1'] = 'experiment.v1'
    experiment_id: Identifier
    hypothesis: Literal['contract-adapter-preserves-baseline-selection']
    baseline_digest: Digest
    candidate_digest: Digest
    dataset_digest: Digest
    evaluator_digest: Digest
    evidence_class: Literal['synthetic-conformance-and-local-microbenchmark']
    state: Literal['proposed', 'evaluated', 'rejected']
    decision: Literal['no-production-promotion'] = 'no-production-promotion'
    observation_count: Annotated[int, Field(ge=1)]


def validate_proposal(request: DecisionRequest, decision: Decision, catalogue: Catalogue, *, now: int):
    """Compatibility check only; even True never grants execution permission."""
    if request.request_id != decision.request_id or request.policy_digest != decision.policy_digest:
        raise ValueError('request/policy mismatch')
    if not (request.registry_digest == decision.registry_digest == catalogue.digest()):
        raise ValueError('registry mismatch')
    if now >= decision.expires_unix:
        raise ValueError('expired proposal')
    if len(decision.steps) > request.max_steps:
        raise ValueError('step budget exceeded')
    capabilities = {c.capability_id for c in catalogue.capabilities}
    if any(s.capability_id not in capabilities for s in decision.steps):
        raise ValueError('unknown capability')
    return True


CONTRACTS = (Capability, Catalogue, DecisionRequest, Decision, HarnessRun, Outcome, Experiment)
