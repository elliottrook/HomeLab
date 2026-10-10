"""Synthetic-only append-only evidence ledger; never an authorization service."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator
from contracts import Contract, Digest, Experiment, HarnessRun, Outcome, Ref
from paired_evidence import PairedPlan, PairedEvaluation, aggregate


class DatasetCase(Contract):
    case_id: Ref
    family_id: Ref
    input_digest: Digest
    expected_digest: Digest


class Dataset(Contract):
    schema_version: Literal['dataset.v1'] = 'dataset.v1'
    dataset_id: Ref
    cases: Annotated[tuple[DatasetCase, ...], Field(min_length=1, max_length=1000)]
    label_provenance: Literal['synthetic-authored'] = 'synthetic-authored'
    data_class: Literal['synthetic'] = 'synthetic'

    @model_validator(mode='after')
    def unique_cases(self):
        if len({c.case_id for c in self.cases}) != len(self.cases):
            raise ValueError('duplicate dataset case')
        return self


class RegisteredRun(Contract):
    schema_version: Literal['registered-run.v1'] = 'registered-run.v1'
    dataset_digest: Digest
    case_id: Ref
    candidate_role: Literal['baseline', 'candidate']
    run: HarnessRun


class LinkedOutcome(Contract):
    schema_version: Literal['linked-outcome.v1'] = 'linked-outcome.v1'
    experiment_id: Ref
    run_event_digest: Digest
    outcome: Outcome


class Evaluation(Contract):
    schema_version: Literal['evaluation.v1'] = 'evaluation.v1'
    experiment_id: Ref
    evaluator_digest: Digest
    dataset_digest: Digest
    candidate_digest: Digest
    independent_units: Annotated[int, Field(ge=1, le=1000000)]
    passed_units: Annotated[int, Field(ge=0, le=1000000)]
    verdict: Literal['pass', 'fail', 'inconclusive']
    label_provenance: Literal['synthetic-authored'] = 'synthetic-authored'
    data_class: Literal['synthetic'] = 'synthetic'


class Review(Contract):
    schema_version: Literal['review.v1'] = 'review.v1'
    experiment_id: Ref
    evaluation_digest: Digest
    reviewer_ref: Ref
    decision: Literal['retain-baseline', 'reject-candidate', 'request-more-evidence']
    reason: Literal['no-measured-benefit', 'guardrail-failed', 'insufficient-evidence']
    execution_authority: Literal['none'] = 'none'
    data_class: Literal['synthetic'] = 'synthetic'


MODELS = {'experiment': Experiment, 'outcome': Outcome, 'evaluation': Evaluation, 'review': Review,
          'dataset': Dataset, 'run': RegisteredRun, 'linked-outcome': LinkedOutcome,
          'paired-plan': PairedPlan, 'paired-evaluation': PairedEvaluation}
ZERO = 'sha256:' + '0'*64


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value):
    return 'sha256:' + hashlib.sha256(canonical(value).encode()).hexdigest()


class EvidenceStore:
    def __init__(self, path):
        self.path = Path(path)
        # The caller owns this disposable path; never create a service or default location.
        self.connection = sqlite3.connect(str(path), timeout=1.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript('''
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                record_json TEXT NOT NULL,
                previous_digest TEXT NOT NULL,
                event_digest TEXT NOT NULL UNIQUE
            );
            CREATE TRIGGER IF NOT EXISTS evidence_no_update BEFORE UPDATE ON events
                BEGIN SELECT RAISE(ABORT, 'evidence is append-only'); END;
            CREATE TRIGGER IF NOT EXISTS evidence_no_delete BEFORE DELETE ON events
                BEGIN SELECT RAISE(ABORT, 'evidence is append-only'); END;
        ''')
        self.connection.commit()
        self.verify()

    def close(self):
        self.connection.close()

    def records(self, kind=None):
        rows = self.connection.execute('SELECT * FROM events ORDER BY sequence').fetchall()
        return [dict(row) | {'record':json.loads(row['record_json'])} for row in rows
                if kind is None or row['kind'] == kind]

    def _validate(self, kind, record):
        if kind not in MODELS:
            raise ValueError('unknown evidence kind')
        model = MODELS[kind].model_validate_json(canonical(record))
        if isinstance(model, Evaluation) and model.passed_units > model.independent_units:
            raise ValueError('invalid evaluation denominator')
        return model.model_dump(mode='json')

    def _relationships(self, kind, record, prior):
        experiment_id = record.get('experiment_id') or record.get('run',{}).get('experiment_id')
        if kind in {'run','linked-outcome','paired-evaluation','evaluation','paired-plan'} and any(
                p['kind'] in {'review','paired-evaluation'} and p['record']['experiment_id']==experiment_id for p in prior):
            raise ValueError('experiment already reviewed or finalized; use a new experiment')
        if kind == 'paired-plan':
            if not any(p['kind']=='experiment' and p['record']['experiment_id']==experiment_id for p in prior):
                raise ValueError('paired plan needs frozen experiment')
            if any((p['kind']=='paired-plan' and p['record']['experiment_id']==experiment_id) or
                   (p['kind']=='run' and p['record']['run']['experiment_id']==experiment_id) for p in prior):
                raise ValueError('paired plan must precede all runs and be unique')
        elif kind == 'paired-evaluation':
            derived, _ = aggregate(record, prior, digest)
            if any(record[k]!=v for k,v in derived.items()):
                raise ValueError('paired totals differ from measured evidence')
        if kind == 'dataset':
            if any(p['kind']=='dataset' and p['record']['dataset_id']==record['dataset_id'] for p in prior):
                raise ValueError('dataset manifest already frozen')
        elif kind == 'run':
            run=record['run']
            specs=[p['record'] for p in prior if p['kind']=='experiment'
                   and p['record']['experiment_id']==run['experiment_id']]
            if len(specs)!=1 or specs[0]['dataset_digest']!=record['dataset_digest']:
                raise ValueError('run needs matching frozen experiment and dataset')
            if any(p['kind']=='review' and p['record']['experiment_id']==run['experiment_id'] for p in prior):
                raise ValueError('experiment already reviewed; use a new experiment')
            manifests=[p['record'] for p in prior if p['kind']=='dataset'
                       and digest(p['record'])==record['dataset_digest']]
            if len(manifests)!=1 or record['case_id'] not in {c['case_id'] for c in manifests[0]['cases']}:
                raise ValueError('run needs registered dataset case')
            if run['harness_digest']!=specs[0][record['candidate_role']+'_digest']:
                raise ValueError('run harness differs from frozen artifact')
            if any(p['kind']=='run' and p['record']['run']['run_id']==run['run_id'] for p in prior):
                raise ValueError('run identity already registered')
        elif kind == 'linked-outcome':
            runs=[p['record']['run'] for p in prior if p['kind']=='run'
                  and p['event_digest']==record['run_event_digest']]
            if len(runs)!=1 or runs[0]['experiment_id']!=record['experiment_id'] or runs[0]['run_id']!=record['outcome']['run_id']:
                raise ValueError('outcome needs exact registered run')
            if any(p['kind']=='review' and p['record']['experiment_id']==record['experiment_id'] for p in prior):
                raise ValueError('experiment already reviewed; use a new experiment')
            if any(p['kind']=='linked-outcome' and p['record']['run_event_digest']==record['run_event_digest'] for p in prior):
                raise ValueError('run outcome already recorded')
        elif kind == 'experiment':
            if record['status'] != 'preregistered':
                raise ValueError('experiments enter ledger only as preregistered')
            if any(p['kind']=='experiment' and p['record']['experiment_id']==record['experiment_id'] for p in prior):
                raise ValueError('experiment specification already frozen')
        elif kind == 'evaluation':
            if any(p['kind']=='review' and p['record']['experiment_id']==record['experiment_id'] for p in prior):
                raise ValueError('experiment already reviewed; use a new experiment')
            experiments=[p['record'] for p in prior if p['kind']=='experiment'
                         and p['record']['experiment_id']==record['experiment_id']]
            if len(experiments)!=1:
                raise ValueError('evaluation needs a frozen experiment')
            for key in ('evaluator_digest','dataset_digest','candidate_digest'):
                if record[key]!=experiments[0][key]:
                    raise ValueError('evaluation changed frozen provenance')
        elif kind == 'review':
            matches=[p for p in prior if p['kind'] in {'evaluation','paired-evaluation'} and p['event_digest']==record['evaluation_digest']]
            if len(matches)!=1 or matches[0]['record']['experiment_id']!=record['experiment_id']:
                raise ValueError('review needs the exact evaluation event')
            if any(p['kind']=='review' and p['record']['experiment_id']==record['experiment_id'] for p in prior):
                raise ValueError('review already recorded; use a new experiment')

    def append(self, event_id, kind, record):
        # Event identifiers are validated using the same bounded opaque-reference model.
        class EventId(Contract):
            value: Ref
        EventId(value=event_id)
        normalized=self._validate(kind,record)
        self.connection.execute('BEGIN IMMEDIATE')
        try:
            self.verify()
            existing=self.connection.execute('SELECT * FROM events WHERE event_id=?',(event_id,)).fetchone()
            if existing is not None:
                if existing['kind']!=kind or existing['record_json']!=canonical(normalized):
                    raise ValueError('event id reused with different contents')
                self.connection.commit()
                return existing['event_digest']
            prior=self.records()
            self._relationships(kind,normalized,prior)
            previous=prior[-1]['event_digest'] if prior else ZERO
            event_digest=digest({'event_id':event_id,'kind':kind,'record':normalized,'previous_digest':previous})
            self.connection.execute('INSERT INTO events(event_id,kind,record_json,previous_digest,event_digest) VALUES(?,?,?,?,?)',
                                    (event_id,kind,canonical(normalized),previous,event_digest))
            self.connection.commit()
            return event_digest
        except BaseException:
            self.connection.rollback()
            raise

    def verify(self, expected_head=None):
        previous=ZERO
        prior=[]
        for row in self.records():
            record=self._validate(row['kind'],row['record'])
            if canonical(record)!=row['record_json']:
                raise ValueError('noncanonical or altered evidence')
            self._relationships(row['kind'],record,prior)
            expected=digest({'event_id':row['event_id'],'kind':row['kind'],'record':record,'previous_digest':previous})
            if row['previous_digest']!=previous or row['event_digest']!=expected:
                raise ValueError('evidence chain mismatch')
            previous=expected
            prior.append(row)
        if expected_head is not None and previous!=expected_head:
            raise ValueError('ledger differs from external checkpoint')
        return previous

    def backup(self, destination):
        # Never overwrite a recovery artifact; pin its verified head independently.
        path=Path(destination)
        with path.open('xb'):
            pass
        target=sqlite3.connect(str(path))
        try:
            self.connection.backup(target)
        finally:
            target.close()
        restored=EvidenceStore(path)
        try:
            return restored.verify()
        finally:
            restored.close()
