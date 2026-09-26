"""Reviewed local source pin, checked before any extraction or compilation."""
import hashlib
from pathlib import Path
from typing import Literal
from contracts import Contract, Digest, Ref

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'services/aster-agent/aster_agent.py'
DEFINITION = Path(__file__).with_name('source-definition.json')


class SourceDefinition(Contract):
    schema_version: Literal['fixture-source-definition.v1']
    source: Literal['services/aster-agent/aster_agent.py']
    expected_digest: Digest
    review_ref: Ref
    scope: Literal['offline-fixture-only']


def read_pinned_source():
    definition_bytes = DEFINITION.read_bytes()
    definition = SourceDefinition.model_validate_json(definition_bytes)
    source = SOURCE.read_bytes()
    observed = 'sha256:'+hashlib.sha256(source).hexdigest()
    if observed!=definition.expected_digest:
        raise ValueError('fixture source differs from reviewed definition; review a new experiment revision')
    return source, dict(expected_digest=definition.expected_digest,observed_digest=observed,
                       definition_digest='sha256:'+hashlib.sha256(definition_bytes).hexdigest(),
                       review_ref=definition.review_ref)
