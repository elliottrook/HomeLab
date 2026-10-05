"""Reconstruct a bounded synthetic export without running its measurement code.

The expected head must come from independent custody to detect replacement.
This checks structure and arithmetic, never measurement authenticity or approval.
"""
import argparse
import json
import re
import tempfile
from pathlib import Path

from evidence_store import EvidenceStore, canonical
from paired_evidence import aggregate
from evidence_store import digest

MAX_BYTES = 2 * 1024 * 1024
MAX_EVENTS = 1000


def unique_object(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def verify_export(path, expected_head):
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', expected_head):
        raise ValueError('invalid external checkpoint')
    with Path(path).open('rb') as source:
        raw = source.read(MAX_BYTES + 1)
    if len(raw)>MAX_BYTES:
        raise ValueError('evidence exceeds offline size limit')
    proof = json.loads(raw, object_pairs_hook=unique_object)
    if proof.get('schema_version') not in {'paired-proof.v1','lineage-proof.v1'} or proof.get('data_class')!='synthetic':
        raise ValueError('unsupported evidence export')
    events = proof.get('events')
    if not isinstance(events,list) or not 1<=len(events)<=MAX_EVENTS:
        raise ValueError('invalid event count')
    if proof.get('final_head')!=expected_head:
        raise ValueError('export differs from external checkpoint')
    with tempfile.TemporaryDirectory() as directory:
        store = EvidenceStore(Path(directory)/'review.db')
        try:
            ids = set()
            evaluations = []
            for i,event in enumerate(events,1):
                if set(event)!={'sequence','event_id','kind','record_json','previous_digest','event_digest','record'}:
                    raise ValueError('unexpected event fields')
                if type(event['sequence']) is not int or event['sequence']!=i or event['event_id'] in ids:
                    raise ValueError('duplicate or unordered event')
                ids.add(event['event_id'])
                if canonical(event['record'])!=event['record_json']:
                    raise ValueError('export record representations differ')
                if event['kind']=='paired-evaluation':
                    totals,details = aggregate(event['record'],store.records(),digest)
                    evaluations.append(dict(event_digest=event['event_digest'],totals=totals,case_details=details))
                h = store.append(event['event_id'],event['kind'],event['record'])
                restored = store.records()[-1]
                if h!=event['event_digest'] or restored['previous_digest']!=event['previous_digest']:
                    raise ValueError('export event chain mismatch')
            store.verify(expected_head=expected_head)
            if proof['schema_version']=='paired-proof.v1':
                if len(evaluations)!=1 or proof.get('totals')!=evaluations[0]['totals'] or proof.get('case_details')!=evaluations[0]['case_details']:
                    raise ValueError('export summary differs from derived evaluation')
            return dict(schema_version='export-verification.v1',event_count=len(events),verified_head=expected_head,
                        evaluations=evaluations,measurement_authenticity='not-established',review_approval='not-granted')
        finally:
            store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('export',type=Path)
    parser.add_argument('--expected-head',required=True)
    args = parser.parse_args()
    print(json.dumps(verify_export(args.export,args.expected_head),indent=2))


if __name__=='__main__':
    main()
