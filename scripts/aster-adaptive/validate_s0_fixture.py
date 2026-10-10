"""Offline S0 workflow specification checker. Fixtures only; never intake or authority."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from validate_label_batch import (CLASSES, FORBIDDEN, exact, identifier, reject,
                                 unique, validate as validate_labels)

PROTOCOL = 'c384f8d:0b516bd8ede0c65ad26ad640b7b251181565a456956a02f0d2624316f6bb758f'
MAX_BYTES = 256 * 1024
CODES = {'missing-context', 'ambiguous-intent', 'capability-boundary', 'privacy-class',
         'unavailable-capability', 'factual-dispute', 'label-conflict', 'effort-limit',
         'other-unresolved'}
FIELDS = {
    'case': {'revision', 'stratum', 'request_text', 'context_text', 'origin', 'split'},
    'content-review': {'case_ref', 'checks', 'decision'},
    'label': {'case_ref', 'review_ref', 'pass', 'labels', 'uncertainty', 'seconds'},
    'adjudication': {'a_ref', 'b_ref', 'decision', 'final_ref', 'disagreements'},
    'freeze': {'case_ref', 'adjudication_ref', 'final_ref', 'split', 'acceptance_ref'},
    'audit': {'sequence', 'prior_ref', 'target_ref', 'event'},
}
COMMON = {'schema_version', 'record_id', 'case_id', 'family_id', 'actor_ref',
          'created_at', 'supersedes_id', 'data'}
CHECKS = {'no_real_context', 'no_identifiers', 'no_secrets', 'synthetic_only'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def stamp(value):
    reject(type(value) is not str, 'invalid timestamp')
    parsed = datetime.fromisoformat(value)
    reject(parsed.tzinfo is None or parsed.utcoffset() is None, 'timezone required')
    return parsed


def codes(value):
    reject(type(value) is not list or any(type(x) is not str for x in value), 'invalid codes')
    reject(len(set(value)) != len(value) or not set(value) <= CODES, 'invalid codes')


def validate(batch):
    exact(batch, {'schema_version', 'protocol_ref', 'mode', 'retention_ack', 'records'})
    reject(batch['schema_version'] != 's0-workflow-fixture.v1' or
           batch['protocol_ref'] != PROTOCOL, 'unknown contract')
    reject(batch['mode'] != 'synthetic-fixture-only', 'collection disabled')
    reject(batch['retention_ack'] != 'fixture-only-no-human-acceptance', 'human retention unverified')
    rows = batch['records']
    reject(type(rows) is not list or len(rows) > 300, 'invalid count')
    records = {}; latest = {}; states = {}; splits = {}; families = {}; times = {}
    audits = []; frozen = {}; unresolved = 0; started = None

    def ref(value, kind, current):
        exact(value, {'record_id', 'sha256'})
        identifier(value['record_id'])
        target = records.get(value['record_id'])
        reject(target is None or target['schema_version'] != 's0.' + kind + '.v1', 'bad reference type/order')
        reject(value['sha256'] != digest(target), 'reference hash mismatch')
        reject((target['case_id'], target['family_id']) !=
               (current['case_id'], current['family_id']), 'cross-case reference')
        reject(stamp(target['created_at']) > stamp(current['created_at']), 'reference from future')
        return target

    for row in rows:
        exact(row, COMMON)
        for key in ('record_id', 'case_id', 'family_id', 'actor_ref'):
            identifier(row[key])
        reject(not row['actor_ref'].startswith('fixture-'), 'human identity not accepted')
        reject(row['record_id'] in records, 'duplicate record')
        kind = next((k for k in FIELDS if row['schema_version'] == 's0.' + k + '.v1'), None)
        reject(kind is None, 'unknown record type')
        data = row['data']; exact(data, FIELDS[kind])
        cid = row['case_id']; fid = row['family_id']; now = stamp(row['created_at'])
        reject(cid in times and now < times[cid], 'time reversal')
        if started is None: started = now
        reject(now < started or (now - started).total_seconds() > 30 * 86400, 'fixture pilot window exceeded')
        times[cid] = now
        reject(cid in families and families[cid] != fid, 'case family changed')
        families[cid] = fid
        reject(len(set(families.values())) > 30, 'family cap')
        prior = row['supersedes_id']
        if prior is not None:
            identifier(prior)
            old = records.get(prior)
            reject(old is None or old['schema_version'] != row['schema_version'] or
                   old['case_id'] != cid, 'invalid supersession')
            reject(kind != 'case', 'corrections require new case revision')
        state = states.get(cid, 'absent')
        if kind == 'case':
            reject(type(data['revision']) is not int or data['revision'] < 1, 'invalid revision')
            reject(data['stratum'] not in CLASSES or data['split'] not in ('train', 'dev'), 'invalid class/split')
            reject(data['origin'] != 'synthetic-test-fixture', 'human case collection disabled')
            for name, limit in (('request_text', 512), ('context_text', 1024)):
                reject(type(data[name]) is not str or len(data[name]) > limit, 'invalid content size')
            # Payloads are deliberately non-natural-language sentinels, never pilot content.
            reject(data['request_text'] != '[SYNTHETIC TEST FIXTURE]' or data['context_text'] != '', 'nonfixture content prohibited')
            if cid in latest:
                old = latest[cid]
                reject(prior != old['record_id'] or data['revision'] != old['data']['revision'] + 1, 'stale revision')
            else:
                reject(prior is not None or data['revision'] != 1, 'invalid initial revision')
            reject(fid in splits and splits[fid] != data['split'], 'family split leakage')
            splits[fid] = data['split']; latest[cid] = row
            frozen.pop(cid, None); states[cid] = 'draft'
        else:
            reject(cid not in latest, 'case missing')
            case = latest[cid]
            if kind in ('content-review', 'label', 'freeze'):
                reject(ref(data['case_ref'], 'case', row) != case, 'stale case reference')
            if kind == 'content-review':
                reject(state != 'draft', 'review transition')
                reject((now - stamp(case['created_at'])).total_seconds() > 7 * 86400, 'fixture draft expired')
                exact(data['checks'], CHECKS)
                reject(any(type(v) is not bool for v in data['checks'].values()), 'invalid content checks')
                reject(data['decision'] not in ('accept', 'reject', 'uncertain'), 'invalid review')
                reject(data['decision'] == 'accept' and not all(data['checks'].values()), 'review checks missing')
                states[cid] = 'reviewed' if data['decision'] == 'accept' else 'excluded'
            elif kind == 'label':
                reject(state not in ('reviewed', 'labeled-a'), 'label transition')
                review = ref(data['review_ref'], 'content-review', row)
                reject(review['data']['case_ref'] != data['case_ref'] or review['data']['decision'] != 'accept', 'review not accepted')
                reject(data['pass'] != ('A' if state == 'reviewed' else 'B'), 'label pass order')
                codes(data['uncertainty'])
                reject(type(data['seconds']) is not int or not 0 <= data['seconds'] <= 86400, 'invalid effort')
                validate_labels({'schema_version': 'label-batch.v1', 'protocol': 'm3-human-labels-draft-v1',
                                 'data_class': 'synthetic-design-only', 'rows': [{
                    'case_id': cid, 'family_id': fid, 'split': case['data']['split'],
                    'category': case['data']['stratum'], 'content_ref': case['record_id'],
                    'origin': 'synthetic_fixture', 'retention': 'synthetic-git',
                    'content_review': 'synthetic-fixture-only', 'labels': data['labels']}]})
                reject(data['labels'] is None or data['labels']['provenance'] != 'synthetic-test' or
                       data['labels']['adjudication'] != 'synthetic-fixture-only', 'fixture label required')
                states[cid] = 'labeled-' + data['pass'].lower()
            elif kind == 'adjudication':
                reject(state not in ('labeled-a', 'labeled-b'), 'adjudication transition')
                a = ref(data['a_ref'], 'label', row)
                b = ref(data['b_ref'], 'label', row) if data['b_ref'] is not None else None
                reject(a['data']['pass'] != 'A' or a['data']['case_ref']['record_id'] != case['record_id'], 'stale A')
                reject((state == 'labeled-b') != (b is not None), 'missing B')
                if b:
                    reject(b['data']['pass'] != 'B' or b['data']['case_ref'] != a['data']['case_ref'], 'stale B')
                codes(data['disagreements'])
                reject(data['decision'] not in ('accept-personalized', 'accept-dual-reviewed', 'unresolved', 'exclude'), 'invalid adjudication')
                if data['decision'] == 'accept-dual-reviewed':
                    reject(b is None or b['actor_ref'] == a['actor_ref'], 'independence missing')
                if data['decision'].startswith('accept-'):
                    final = ref(data['final_ref'], 'label', row)
                    reject(final not in (a, b), 'unbound final label')
                    states[cid] = 'adjudicated'
                else:
                    reject(data['final_ref'] is not None, 'unresolved final label')
                    states[cid] = 'excluded'; unresolved += 1
            elif kind == 'freeze':
                reject(state != 'adjudicated', 'freeze transition')
                adj = ref(data['adjudication_ref'], 'adjudication', row)
                reject(adj['data']['final_ref'] != data['final_ref'], 'freeze final mismatch')
                final = ref(data['final_ref'], 'label', row)
                reject(final['data']['case_ref'] != data['case_ref'], 'stale frozen label')
                reject(data['split'] != case['data']['split'], 'freeze split mismatch')
                reject(data['acceptance_ref'] != 'fixture-not-human-acceptance', 'human acceptance unverified')
                states[cid] = 'frozen'; frozen[cid] = row['record_id']
            elif kind == 'audit':
                reject(type(data['sequence']) is not int or data['sequence'] != len(audits) + 1, 'audit sequence')
                reject(data['prior_ref'] != (audits[-1] if audits else None), 'audit chain')
                target = records.get(data['target_ref'])
                reject(target is None or target['case_id'] != cid or target['family_id'] != fid or
                       target['schema_version'] == 's0.audit.v1', 'invalid audit target')
                reject(data['event'] != target['schema_version'].split('.')[1], 'audit event mismatch')
                audits.append(row['record_id'])
        records[row['record_id']] = row
    return {'schema_version': 's0-fixture-validation.v1', 'fixture_records': len(rows),
            'fixture_families': len(splits), 'fixture_frozen': len(frozen),
            'fixture_unresolved': unresolved, 'human_labels_verified': 0,
            'collection_authorized': False, 'evaluation_authorized': False,
            'staging_authorized': False, 'human_retention_accepted': False,
            'limitations': ['Fixture structural checks only; no human authenticity or content privacy proof',
                            'No writes, staging, collection, execution, or evaluation']}


def validate_file(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    reject(len(raw) > MAX_BYTES, 'oversized input')
    return validate(json.loads(raw, object_pairs_hook=unique,
                               parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid number'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_file(args.fixture), sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise SystemExit('Fixture rejected; no input content printed')
