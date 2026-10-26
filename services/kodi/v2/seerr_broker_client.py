"""Credential-free Seerr broker boundary with a durable no-retry fence.

Network transport is injected.  This module never knows a Seerr URL or secret.
"""
import hashlib
import json
import os
from pathlib import Path
import re

from seerr_request_model import candidate, result


class BrokerUnavailable(RuntimeError):
    pass


def require(ok, code):
    if not ok:
        raise BrokerUnavailable(code)


def candidate_page(value, expected_query):
    require(isinstance(expected_query, str) and 1 <= len(expected_query) <= 100
            and expected_query == expected_query.strip(), 'seerr-query-invalid')
    require(type(value) is dict and set(value) == {'schema', 'query', 'candidates'}
            and value['schema'] == 1 and value['query'] == expected_query
            and type(value['candidates']) is list
            and len(value['candidates']) <= 24, 'seerr-page-schema')
    items = tuple(candidate(item) for item in value['candidates'])
    require(len({item.identity for item in items}) == len(items),
            'seerr-page-duplicate')
    return items


def _atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    with open(temporary, 'wb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class RequestWriter:
    """Submit one explicit proposal; uncertain outcomes remain fenced on disk."""

    def __init__(self, journal_root, send):
        self.root = Path(journal_root)
        self.send = send

    def _path(self, identity):
        require(isinstance(identity, str)
                and re.fullmatch(r'seerr:(movie|tv):[1-9][0-9]{0,9}', identity),
                'seerr-write-identity')
        return self.root/(identity.replace(':', '-')+'.json')

    def submit(self, proposal):
        require(getattr(proposal, 'state', None) == 'ready'
                and type(getattr(proposal, 'payload', None)) is dict,
                'seerr-write-not-ready')
        payload = proposal.payload
        identity = payload.get('candidate_id')
        path = self._path(identity)
        digest = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if path.exists():
            try:
                prior = json.loads(path.read_text())
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise BrokerUnavailable('seerr-write-journal-invalid') from exc
            require(prior.get('payload_sha256') == digest,
                    'seerr-write-identity-reused')
            if prior.get('status') == 'committed':
                return result(prior.get('result'), identity)
            raise BrokerUnavailable('seerr-write-recovery-required')
        record = {'schema': 1, 'candidate_id': identity,
                  'payload_sha256': digest, 'status': 'prepared', 'result': None}
        _atomic(path, record)
        try:
            response = self.send(dict(payload))
            accepted = result(response, identity)
        except Exception as exc:
            record['status'] = 'uncertain'
            _atomic(path, record)
            raise BrokerUnavailable('seerr-write-outcome-uncertain') from exc
        record.update(status='committed', result=accepted)
        _atomic(path, record)
        return dict(accepted)
