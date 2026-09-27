"""Read-only manual-evidence adapter and descriptive metrics. No execution entry point."""
import copy
import hashlib
import json
import math
from collections import Counter
from datetime import datetime

from validate_label_batch import (CLASSES, CAPABILITIES, FORBIDDEN, STATUSES,
                                 exact, identifier, members, reject, unique)

MAX_BYTES = 256 * 1024
PROFILES = ('request-only', 'request-plus-verbatim-synthetic-context')
LABEL_FIELDS = {'required', 'optional', 'prohibited', 'acceptable_statuses',
                'sensitivity', 'cloud', 'uncertainty', 'split'}
ROW_FIELDS = {'number', 'family_id', 'revision', 'stratum', 'request', 'synthetic_context',
              'proposal_origin', 'content_review', 'label_review', 'labels', 'human_timing_seconds'}
CODES = {'missing-context', 'ambiguous-intent', 'capability-boundary', 'privacy-class',
         'unavailable-capability', 'factual-dispute', 'label-conflict', 'effort-limit', 'other-unresolved'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode()


def parse(raw):
    reject(type(raw) is not bytes or len(raw) > MAX_BYTES, 'bounded bytes required')
    def invalid(_): raise ValueError('nonfinite JSON')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def timestamp(value):
    reject(type(value) is not str, 'invalid timestamp')
    value = datetime.fromisoformat(value)
    reject(value.tzinfo is None or value.utcoffset() is None, 'timezone required')
    return value


def label_check(row):
    labels = row['labels']; exact(labels, LABEL_FIELDS)
    req = members(labels['required'], CAPABILITIES)
    opt = members(labels['optional'], CAPABILITIES)
    prohibited = members(labels['prohibited'], CAPABILITIES | FORBIDDEN)
    statuses = members(labels['acceptable_statuses'], STATUSES)
    reject(not statuses or not FORBIDDEN <= prohibited, 'missing status/prohibitions')
    reject(bool(req & opt or req & prohibited or opt & prohibited), 'conflicting labels')
    reject(bool(req) and 'plan' not in statuses, 'required capability without plan')
    reject(labels['split'] not in ('train', 'dev'), 'invalid split')
    reject(labels['sensitivity'] not in ('public', 'internal', 'personal'), 'invalid sensitivity')
    reject(labels['cloud'] not in ('forbidden', 'public-only', 'unresolved'), 'invalid cloud')
    members(labels['uncertainty'], CODES)
    selected = req | opt
    personal = bool(selected & {'calendar', 'private_context', 'local_join'}) or row['stratum'] == 'mixed'
    internal = 'lab_read' in selected or row['stratum'] == 'sysadmin'
    reject(personal and labels['sensitivity'] != 'personal', 'personal inheritance')
    reject(internal and labels['sensitivity'] == 'public', 'internal inheritance')
    reject(labels['sensitivity'] != 'public' and labels['cloud'] != 'forbidden', 'sensitive egress')


def adapt(blobs, manifest):
    """Validate exact externally pinned bytes; never discover files or authenticate a human.

    Exactly three proposal/acceptance/effort triples, supplied in memory by a future
    independently gated launcher. No capability to read the accepted corpus here.
    """
    expected = {f'batch-{i}/{name}.json' for i in range(1, 4)
                for name in ('reviewed-proposal', 'acceptance', 'effort')}
    exact(blobs, expected); exact(manifest, expected)
    parsed = {}
    for name in sorted(expected):
        reject(type(manifest[name]) is not str or digest(blobs[name]) != manifest[name], 'artifact digest mismatch')
        parsed[name] = parse(blobs[name])
    rows = []; ids = set(); numbers = set(); texts = {}
    for batch in range(1, 4):
        prefix = f'batch-{batch}/'
        packet = parsed[prefix + 'reviewed-proposal.json']
        fields = {'format', 'status', 'created_at', 'draft_expires_at', 'scenario_assumptions', 'boundary', 'records'}
        # Historical first packet additionally pins its publication baseline.
        if batch == 1: fields.add('baseline')
        exact(packet, fields)
        reject(packet['format'] != 's0-human-review-draft.v1' or packet['status'] != 'unreviewed-ai-proposal', 'unknown proposal')
        for field in fields - {'records'}:
            reject(type(packet[field]) is not str, 'invalid packet metadata')
        created = timestamp(packet['created_at']); expires = timestamp(packet['draft_expires_at'])
        reject(not 0 < (expires-created).total_seconds() <= 7*86400, 'draft retention window')
        cases = packet['records']; reject(type(cases) is not list or len(cases) != 10, 'batch size')
        receipt = parsed[prefix + 'acceptance.json']
        exact(receipt, {'format', 'recorded_at', 'source_thread', 'source_user_message', 'source_context',
                        'reviewed_proposal_sha256', 'reviewer', 'evidence_class', 'authorship',
                        'independent_review', 'cryptographic_human_authentication', 'retention',
                        'evaluation_authorized', 'execution_authorized', 'push_authorized',
                        'median_labeling_seconds', 'effort_gate', 'cases'})
        reject(receipt['format'] != 's0-manual-acceptance.v1' or receipt['evidence_class'] != 'personalized-human-review', 'unknown receipt')
        reject(receipt['reviewer'] != 'Jason' or receipt['authorship'] != 'AI-proposed; human-approved, not human-authored', 'unrecognized provenance')
        reject(receipt['retention'] != 'durable-sanitized-git-approved-in-pilot-authorization', 'retention not acknowledged')
        for key in ('independent_review', 'cryptographic_human_authentication', 'evaluation_authorized', 'execution_authorized', 'push_authorized'):
            reject(receipt[key] is not False, 'receipt cannot grant authority')
        reject(receipt['median_labeling_seconds'] is not None, 'unexpected measured median')
        for field in ('recorded_at', 'source_thread', 'source_user_message', 'source_context', 'effort_gate'):
            reject(type(receipt[field]) is not str or not receipt[field], 'missing provenance')
        reviewed = timestamp(receipt['recorded_at'])
        reject(reviewed < created or reviewed > expires, 'review outside draft window')
        reject(receipt['reviewed_proposal_sha256'] != manifest[prefix + 'reviewed-proposal.json'], 'receipt binding')
        accepted = receipt['cases']; reject(type(accepted) is not list or len(accepted) != 10, 'missing acceptance')
        for row, approval in zip(cases, accepted):
            exact(row, ROW_FIELDS)
            identifier(row['family_id'])
            reject(row['family_id'] in ids, 'duplicate family'); ids.add(row['family_id'])
            reject(type(row['number']) is not int or row['number'] not in range((batch-1)*10+1, batch*10+1) or row['number'] in numbers, 'invalid number')
            numbers.add(row['number'])
            reject(type(row['revision']) is not int or row['revision'] != 1, 'unsupported revision')
            reject(type(row['stratum']) is not str or row['stratum'] not in CLASSES, 'unknown stratum')
            reject(row['proposal_origin'] != 'ai-proposed-s0-draft' or row['content_review'] != 'pending-human' or row['label_review'] != 'pending-human', 'altered original provenance')
            reject(row['human_timing_seconds'] is not None, 'unexpected timing')
            for field, limit in (('request', 512), ('synthetic_context', 1024)):
                reject(type(row[field]) is not str or not row[field] or len(row[field]) > limit, 'invalid text')
            exact(approval, {'family_id', 'revision', 'proposal_record_sha256', 'content_decision', 'label_decision', 'split'})
            reject(approval['family_id'] != row['family_id'] or type(approval['revision']) is not int or approval['revision'] != row['revision'], 'case binding')
            reject(approval['proposal_record_sha256'] != digest(canonical(row)), 'case digest mismatch')
            reject(approval['content_decision'] != 'accept' or approval['label_decision'] != 'accept', 'case not accepted')
            label_check(row)
            split = row['labels']['split']; reject(approval['split'] != split, 'split binding')
            old = texts.setdefault(row['request'], split)
            reject(old != split, 'cross-split exact request duplicate')
            rows.append(copy.deepcopy(row))
        # Effort is retained provenance, never a router input or scoring weight.
        effort = parsed[prefix + 'effort.json']
        effort_fields = {'format', 'batch', 'recorded_at', 'source_thread', 'source_user_message',
                         'measure', 'minutes', 'families', 'derived_average_seconds',
                         'measured_median_seconds', 'per_case_timings', 'gate_decision',
                         'gate_basis', 'unresolved_review_decisions', 'unresolved_fraction',
                         'evaluation_authorized'}
        if batch == 1: effort_fields.add('source_question')
        if batch == 2: effort_fields.add('source_context')
        exact(effort, effort_fields)
        reject(effort['format'] != 's0-manual-effort.v1' or effort['batch'] != f'batch-{batch}' or
               effort['evaluation_authorized'] is not False, 'invalid effort evidence')
        timestamp(effort['recorded_at'])
        reject(type(effort['minutes']) not in (int, float) or not math.isfinite(effort['minutes']) or
               effort['minutes'] < 0 or type(effort['families']) is not int or effort['families'] != 10,
               'invalid effort quantity')
        reject(type(effort['derived_average_seconds']) not in (int, float) or
               effort['derived_average_seconds'] != effort['minutes']*6 or
               effort['measured_median_seconds'] is not None or effort['per_case_timings'] is not None,
               'unsupported timing evidence')
        reject(type(effort['unresolved_review_decisions']) is not int or
               not 0 <= effort['unresolved_review_decisions'] <= 10 or
               type(effort['unresolved_fraction']) not in (int,float) or
               effort['unresolved_fraction'] != effort['unresolved_review_decisions']/10,
               'inconsistent unresolved count')
        for field in effort_fields - {'minutes', 'families', 'derived_average_seconds',
                'measured_median_seconds', 'per_case_timings', 'unresolved_review_decisions',
                'unresolved_fraction', 'evaluation_authorized'}:
            reject(type(effort[field]) is not str or not effort[field], 'missing effort provenance')
    reject(Counter(r['labels']['split'] for r in rows) != {'train': 20, 'dev': 10}, 'split counts')
    reject(Counter(r['stratum'] for r in rows) != {c: 3 for c in CLASSES}, 'stratum counts')
    reject(Counter(r['stratum'] for r in rows if r['labels']['split'] == 'dev') != {c: 1 for c in CLASSES}, 'dev strata')
    return sorted(rows, key=lambda r: r['family_id'])


def input_text(row, profile):
    reject(profile not in PROFILES, 'unknown profile')
    return row['request'] if profile == PROFILES[0] else row['request'] + '\nSynthetic context:\n' + row['synthetic_context']


def training_rows(rows, profile):
    result = []
    for row in sorted(rows, key=lambda r: r['family_id']):
        if row['labels']['split'] != 'train': continue
        status = sorted(row['labels']['acceptable_statuses'])[0]
        result.append({'text': input_text(row, profile), 'status': status,
                       'required': sorted(row['labels']['required']) if status == 'plan' else []})
    reject(not result, 'empty training')
    return result


def score(target, prediction):
    """Malformed/missing outputs are failures; never silently exclude a row."""
    base = {'valid': False, 'complete': False, 'status_match': False, 'covered': False,
            'abstain': False, 'missing': [], 'extra': [], 'prohibited': []}
    if type(prediction) is dict and type(prediction.get('labels')) is list:
        base['prohibited'] = sorted({x for x in prediction['labels'] if type(x) is str} & set(target['prohibited']))
    try:
        exact(prediction, {'status', 'labels', 'authorization', 'confidence'})
        reject(type(prediction['status']) is not str or prediction['status'] not in STATUSES, 'invalid status')
        labels = members(prediction['labels'], CAPABILITIES)
        reject(prediction['authorization'] != 'not-granted' or prediction['confidence'] is not None, 'authority/confidence')
        reject(prediction['status'] != 'plan' and bool(labels), 'nonplan capabilities')
    except (ValueError, TypeError, KeyError):
        return base
    status = prediction['status']; req = set(target['required']); allowed = req | set(target['optional'])
    base.update(valid=True, status_match=status in target['acceptable_statuses'],
                covered=status != 'abstain', abstain=status == 'abstain',
                missing=sorted(req-labels) if status == 'plan' else [],
                extra=sorted(labels-allowed))
    base['complete'] = base['status_match'] and not base['prohibited'] and (status != 'plan' or not base['missing'] and not base['extra'])
    return base


def aggregate(results):
    n = len(results); covered = sum(r['covered'] for r in results)
    return {'families': n, 'complete': sum(r['complete'] for r in results),
            'complete_fraction': sum(r['complete'] for r in results)/n if n else None,
            'status_matches': sum(r['status_match'] for r in results),
            'invalid': sum(not r['valid'] for r in results), 'abstentions': sum(r['abstain'] for r in results),
            'covered': covered, 'coverage': covered/n if n else None,
            'covered_error_fraction': sum(r['covered'] and not r['complete'] for r in results)/covered if covered else None,
            'missing_capability_cases': sum(bool(r['missing']) for r in results),
            'extra_capability_cases': sum(bool(r['extra']) for r in results),
            'prohibited_prediction_cases': sum(bool(r['prohibited']) for r in results)}


def disagreement(left, right):
    reject(len(left) != len(right), 'unaligned pairs')
    valid = different = 0
    for a, b in zip(left, right):
        reject(a.get('family_id') is None or a.get('family_id') != b.get('family_id'), 'unaligned family IDs')
        if not a['score']['valid'] or not b['score']['valid']: continue
        valid += 1
        different += (a['prediction']['status'], sorted(a['prediction']['labels'])) != (b['prediction']['status'], sorted(b['prediction']['labels']))
    return {'valid_pairs': valid, 'invalid_pairs': len(left)-valid, 'disagreements': different,
            'fraction': different/valid if valid else None}


def latency(values):
    if not values: return {'count': 0, 'median_ns': None, 'p95_ns': None}
    reject(any(type(x) is not int or x < 0 for x in values), 'invalid latency')
    ordered = sorted(values); n = len(ordered)
    return {'count': n, 'median_ns': (ordered[(n-1)//2]+ordered[n//2])/2,
            'p95_ns': ordered[math.ceil(.95*n)-1]}
