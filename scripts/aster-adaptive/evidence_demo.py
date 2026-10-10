"""Disposable synthetic ledger/restore demonstration; no retrospective preregistration."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from evidence_store import EvidenceStore


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    source=Path(__file__).read_bytes()
    d='sha256:'+hashlib.sha256(source).hexdigest()
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        store=EvidenceStore(root/'ledger.db')
        try:
            store.append('spec','experiment',dict(experiment_id='storage-fixture',owner='fixture-proposer',
                baseline_digest=d,candidate_digest=d,evaluator_digest=d,dataset_digest=d,
                status='preregistered',metric='offline-payload-construction-ms'))
            evaluation=store.append('measurement','evaluation',dict(experiment_id='storage-fixture',
                candidate_digest=d,evaluator_digest=d,dataset_digest=d,independent_units=10,
                passed_units=1,verdict='fail'))
            head=store.append('review','review',dict(experiment_id='storage-fixture',evaluation_digest=evaluation,
                reviewer_ref='fixture-reviewer',decision='retain-baseline',reason='guardrail-failed'))
            backup_head=store.backup(root/'backup.db')
            restored=EvidenceStore(root/'backup.db')
            try:
                assert restored.verify(expected_head=head)==backup_head
                assert len(restored.records())==3
            finally:
                restored.close()
            summary={'schema_version':'storage-proof.v1','data_class':'synthetic',
                     'event_count':3,'external_head':head,'backup_head':backup_head,
                     'restored_head_verified':True,'raw_database_retained':False,
                     'script_digest':d,'limits':['fixture labels are illustrative, not measured harness results',
                        'reviewer references are metadata, not authenticated identity',
                        'hash chain requires independently retained head to detect truncation/replacement']}
        finally:
            store.close()
    args.output.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'events':3,'restore_verified':True,'database_retained':False}))


if __name__=='__main__':
    main()
