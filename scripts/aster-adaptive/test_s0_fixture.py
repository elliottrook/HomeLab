"""Synthetic in-memory specification tests. No pilot cases or human receipts."""
import copy
import json
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_s0_fixture as v


def empty():
    return {'schema_version': 's0-workflow-fixture.v1', 'protocol_ref': v.PROTOCOL,
            'mode': 'synthetic-fixture-only', 'retention_ack': 'fixture-only-no-human-acceptance',
            'records': []}


def workflow():
    batch = empty(); rows = batch['records']

    def add(kind, data, actor='fixture-a'):
        row = {'schema_version': 's0.' + kind + '.v1', 'record_id': 'fixture-' + kind,
               'case_id': 'fixture-case-a', 'family_id': 'fixture-family-a',
               'actor_ref': actor, 'created_at': '2026-09-25T10:00:00+00:00',
               'supersedes_id': None, 'data': data}
        rows.append(row)
        return {'record_id': row['record_id'], 'sha256': v.digest(row)}

    case = add('case', {'revision': 1, 'stratum': 'timer', 'request_text': '[SYNTHETIC TEST FIXTURE]',
                       'context_text': '', 'origin': 'synthetic-test-fixture', 'split': 'train'})
    review = add('content-review', {'case_ref': case, 'checks': dict.fromkeys(v.CHECKS, True), 'decision': 'accept'})
    label = add('label', {'case_ref': case, 'review_ref': review, 'pass': 'A', 'uncertainty': [], 'seconds': 10,
                         'labels': {'provenance': 'synthetic-test', 'required': ['timer'], 'optional': [],
                                    'prohibited': sorted(v.FORBIDDEN), 'acceptable_statuses': ['plan'],
                                    'sensitivity': 'public', 'cloud': 'public-only',
                                    'adjudication': 'synthetic-fixture-only'}})
    adj = add('adjudication', {'a_ref': label, 'b_ref': None, 'decision': 'accept-personalized',
                             'final_ref': label, 'disagreements': []})
    add('freeze', {'case_ref': case, 'adjudication_ref': adj, 'final_ref': label, 'split': 'train',
                   'acceptance_ref': 'fixture-not-human-acceptance'})
    return batch


def rehash(batch):
    """Rebind fixture references after a mutation so semantic checks get exercised."""
    seen = {}
    def walk(value):
        if isinstance(value, dict):
            if set(value) == {'record_id', 'sha256'} and value['record_id'] in seen:
                value['sha256'] = v.digest(seen[value['record_id']])
            else:
                for x in value.values(): walk(x)
        elif isinstance(value, list):
            for x in value: walk(x)
    for row in batch['records']:
        walk(row['data']); seen[row['record_id']] = row


class S0Tests(unittest.TestCase):
    def reject(self, batch):
        with self.assertRaises((ValueError, TypeError)): v.validate(batch)

    def test_empty_never_authorizes(self):
        result = v.validate(empty())
        for key in ('collection_authorized', 'evaluation_authorized', 'staging_authorized', 'human_retention_accepted'):
            self.assertIs(result[key], False)
        self.assertEqual(result['human_labels_verified'], 0)

    def test_fixture_freeze_never_authorizes(self):
        result = v.validate(workflow())
        self.assertEqual(result['fixture_frozen'], 1)
        self.assertFalse(result['collection_authorized'])

    def test_no_network_subprocess_or_writes(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('network')), \
             patch.object(subprocess, 'Popen', side_effect=AssertionError('process')), \
             patch('builtins.open', side_effect=AssertionError('file write/read')):
            v.validate(workflow())

    def test_unknown_envelope_or_human_mode(self):
        for key, value in [('mode', 'human'), ('protocol_ref', 'other'), ('retention_ack', True), ('extra', 1)]:
            batch = empty(); batch[key] = value; self.reject(batch)

    def test_raw_content_origin_actor_and_claims(self):
        for key, value in [('request_text', 'some real text'), ('context_text', 'private'),
                           ('origin', 'human-authored-s0')]:
            batch = workflow(); batch['records'][0]['data'][key] = value; rehash(batch); self.reject(batch)
        batch = workflow(); batch['records'][0]['actor_ref'] = 'jason'; self.reject(batch)
        batch = workflow(); batch['records'][0]['human_verified'] = True; self.reject(batch)

    def test_review_checks_required(self):
        for value in (False, 1, None):
            batch = workflow(); batch['records'][1]['data']['checks']['no_secrets'] = value
            rehash(batch); self.reject(batch)
        for decision in ('reject', 'uncertain'):
            batch = workflow(); batch['records'][1]['data']['decision'] = decision
            rehash(batch); self.reject(batch)

    def test_missing_review_and_out_of_order(self):
        batch = workflow(); del batch['records'][1]; self.reject(batch)
        batch = workflow(); batch['records'][1:3] = reversed(batch['records'][1:3]); self.reject(batch)

    def test_reference_hash_and_wrong_type(self):
        batch = workflow(); batch['records'][2]['data']['review_ref']['sha256'] = '0' * 64; self.reject(batch)
        batch = workflow(); batch['records'][2]['data']['review_ref'] = copy.deepcopy(batch['records'][2]['data']['case_ref']); self.reject(batch)

    def test_optional_sensitive_privacy(self):
        for cap in ('calendar', 'private_context', 'local_join', 'lab_read'):
            batch = workflow(); batch['records'][2]['data']['labels']['optional'] = [cap]
            rehash(batch); self.reject(batch)

    def test_forbidden_conflicting_or_human_labels(self):
        for key, value in [('prohibited', []), ('optional', ['timer']), ('provenance', 'human'),
                           ('adjudication', 'human-verified')]:
            batch = workflow(); batch['records'][2]['data']['labels'][key] = value
            rehash(batch); self.reject(batch)

    def test_dual_requires_second_human_even_fixture(self):
        batch = workflow(); batch['records'][3]['data']['decision'] = 'accept-dual-reviewed'
        rehash(batch); self.reject(batch)

    def test_unresolved_cannot_freeze(self):
        batch = workflow(); batch['records'][3]['data'].update(decision='unresolved', final_ref=None)
        rehash(batch); self.reject(batch)
        batch['records'].pop()
        self.assertEqual(v.validate(batch)['fixture_unresolved'], 1)

    def test_split_and_revision_rules(self):
        for split in ('test', 'calibration'):
            batch = workflow(); batch['records'][0]['data']['split'] = split; rehash(batch); self.reject(batch)
        batch = workflow(); newer = copy.deepcopy(batch['records'][0]); newer['record_id'] = 'fixture-case-next'
        newer['supersedes_id'] = batch['records'][0]['record_id']; newer['data']['revision'] = 2
        batch['records'].append(newer)
        self.assertEqual(v.validate(batch)['fixture_frozen'], 0)
        newer['data']['split'] = 'dev'; self.reject(batch)
        newer['data']['split'] = 'train'; newer['data']['revision'] = 3; self.reject(batch)

    def test_duplicate_cross_case_reference(self):
        batch = workflow(); batch['records'].append(copy.deepcopy(batch['records'][0])); self.reject(batch)
        batch = workflow(); batch['records'][1]['case_id'] = 'fixture-other'; self.reject(batch)

    def test_bad_time_and_boolean_integer(self):
        batch = workflow(); batch['records'][1]['created_at'] = '2026-09-24T10:00:00+00:00'; self.reject(batch)
        batch = workflow(); batch['records'][0]['created_at'] = '2026-09-25'; self.reject(batch)
        batch = workflow(); batch['records'][2]['data']['seconds'] = True; self.reject(batch)

    def test_bad_freeze_and_acceptance(self):
        for key, value in [('split', 'dev'), ('acceptance_ref', 'human-approved')]:
            batch = workflow(); batch['records'][4]['data'][key] = value; self.reject(batch)

    def test_file_bounds_duplicates_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.json'
            for content in ('{"a":1,"a":2}', '{"a":NaN}', 'x' * (v.MAX_BYTES + 1)):
                path.write_text(content)
                with self.assertRaises(ValueError): v.validate_file(path)
            path.write_text(json.dumps(empty()))
            self.assertFalse(v.validate_file(path)['collection_authorized'])

    def test_draft_and_pilot_windows(self):
        batch = workflow()
        for row in batch['records'][1:]: row['created_at'] = '2026-10-03T10:00:00+00:00'
        rehash(batch); self.reject(batch)
        batch = workflow(); row = copy.deepcopy(batch['records'][0])
        row.update(record_id='fixture-new', case_id='fixture-new', family_id='fixture-new',
                   created_at='2026-10-26T10:00:00+00:00')
        batch['records'].append(row); self.reject(batch)

    def test_stale_review_after_revision(self):
        batch = workflow(); revision = copy.deepcopy(batch['records'][0])
        revision.update(record_id='fixture-revised', supersedes_id='fixture-case')
        revision['data']['revision'] = 2
        batch['records'].insert(2, revision)
        self.reject(batch)

    def test_same_actor_cannot_dual_review(self):
        batch = workflow(); second = copy.deepcopy(batch['records'][2])
        second['record_id'] = 'fixture-label-b'; second['data']['pass'] = 'B'
        batch['records'].insert(3, second)
        batch['records'][4]['data'].update(decision='accept-dual-reviewed',
            b_ref={'record_id': second['record_id'], 'sha256': v.digest(second)})
        rehash(batch); self.reject(batch)
        second['actor_ref'] = 'fixture-b'; rehash(batch)
        self.assertEqual(v.validate(batch)['fixture_frozen'], 1)

    def test_audit_chain_and_targets(self):
        batch = workflow(); audit = copy.deepcopy(batch['records'][0])
        audit.update(schema_version='s0.audit.v1', record_id='fixture-audit',
                     data={'sequence': 1, 'prior_ref': None, 'target_ref': 'fixture-freeze', 'event': 'freeze'})
        batch['records'].append(audit); v.validate(batch)
        for key, value in [('sequence', True), ('prior_ref', 'absent'), ('target_ref', 'absent'), ('event', 'case')]:
            other = copy.deepcopy(batch); other['records'][-1]['data'][key] = value; self.reject(other)

    def test_family_split_across_cases(self):
        batch = workflow(); other = copy.deepcopy(batch['records'][0])
        other.update(record_id='fixture-other', case_id='fixture-other')
        other['data']['split'] = 'dev'; batch['records'].append(other); self.reject(batch)

    def test_family_and_record_caps(self):
        batch = empty(); batch['records'] = [None] * 301; self.reject(batch)
        batch = empty()
        for i in range(31):
            row = copy.deepcopy(workflow()['records'][0])
            row.update(record_id='fixture-r-' + str(i), case_id='fixture-c-' + str(i), family_id='fixture-f-' + str(i))
            batch['records'].append(row)
        self.reject(batch)


if __name__ == '__main__': unittest.main()
