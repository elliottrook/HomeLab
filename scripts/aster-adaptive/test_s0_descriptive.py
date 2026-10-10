"""In-memory invented fixtures only: never reads accepted pilot records."""
import copy
import json
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import s0_descriptive as d
import s0_descriptive_runner as r


def fixture_row(i, split='train', stratum='timer'):
    sensitive = 'personal' if stratum=='mixed' else 'internal' if stratum=='sysadmin' else 'public'
    return {'number': i+1, 'family_id': f'fixture-{i:02d}', 'revision':1, 'stratum':stratum,
            'request': f'[FIXTURE] timer example {i}', 'synthetic_context': f'[FIXTURE] scenario {i}',
            'proposal_origin':'ai-proposed-s0-draft','content_review':'pending-human',
            'label_review':'pending-human','human_timing_seconds':None,
            'labels':{'required':['timer'],'optional':[], 'prohibited':sorted(d.FORBIDDEN),
                      'acceptable_statuses':['plan'], 'sensitivity':sensitive,
                      'cloud':'forbidden', 'uncertainty':[], 'split':split}}


def evidence():
    """Fabricated schema receipts only; not actual human records or pilot cases."""
    blobs={};manifest={};strata=sorted(d.CLASSES)
    for batch in range(1,4):
        rows=[fixture_row((batch-1)*10+j, 'dev' if batch==3 else 'train', strata[j]) for j in range(10)]
        packet={'format':'s0-human-review-draft.v1','status':'unreviewed-ai-proposal',
                'created_at':'2026-09-26T09:00:00-07:00','draft_expires_at':'2026-10-03T09:00:00-07:00','scenario_assumptions':'fixture',
                'boundary':'fixture','records':rows}
        if batch==1: packet['baseline']='fixture'
        raw=json.dumps(packet).encode()
        receipt={'format':'s0-manual-acceptance.v1','recorded_at':'2026-09-26T10:00:00-07:00','source_thread':'fixture',
                 'source_user_message':'fixture-not-an-approval','source_context':'fixture',
                 'reviewed_proposal_sha256':d.digest(raw),'reviewer':'Jason',
                 'evidence_class':'personalized-human-review',
                 'authorship':'AI-proposed; human-approved, not human-authored',
                 'independent_review':False,'cryptographic_human_authentication':False,
                 'retention':'durable-sanitized-git-approved-in-pilot-authorization',
                 'evaluation_authorized':False,'execution_authorized':False,'push_authorized':False,
                 'median_labeling_seconds':None,'effort_gate':'fixture','cases':[]}
        for row in rows:
            receipt['cases'].append({'family_id':row['family_id'],'revision':1,
                'proposal_record_sha256':d.digest(d.canonical(row)),
                'content_decision':'accept','label_decision':'accept','split':row['labels']['split']})
        blobs[f'batch-{batch}/reviewed-proposal.json']=raw
        blobs[f'batch-{batch}/acceptance.json']=json.dumps(receipt).encode()
        effort={'format':'s0-manual-effort.v1','batch':f'batch-{batch}',
                'recorded_at':'2026-09-26T10:00:00-07:00','source_thread':'fixture',
                'source_user_message':'fixture','measure':'fixture', 'minutes':1,'families':10,
                'derived_average_seconds':6,'measured_median_seconds':None,'per_case_timings':None,
                'gate_decision':'fixture','gate_basis':'fixture','unresolved_review_decisions':0,
                'unresolved_fraction':0,'evaluation_authorized':False}
        if batch==1:effort['source_question']='fixture'
        if batch==2:effort['source_context']='fixture'
        blobs[f'batch-{batch}/effort.json']=json.dumps(effort).encode()
    manifest={name:d.digest(raw) for name,raw in blobs.items()}
    return blobs,manifest


def mutate(blobs, manifest, name, change):
    value=json.loads(blobs[name]);change(value)
    blobs[name]=json.dumps(value).encode();manifest[name]=d.digest(blobs[name])


def change_case(blobs, manifest, batch, index, change):
    packet_name=f'batch-{batch}/reviewed-proposal.json'
    packet=json.loads(blobs[packet_name]);change(packet['records'][index])
    blobs[packet_name]=json.dumps(packet).encode();manifest[packet_name]=d.digest(blobs[packet_name])
    receipt_name=f'batch-{batch}/acceptance.json';receipt=json.loads(blobs[receipt_name])
    receipt['reviewed_proposal_sha256']=manifest[packet_name]
    row=packet['records'][index]
    receipt['cases'][index].update(family_id=row['family_id'], revision=row['revision'],
        proposal_record_sha256=d.digest(d.canonical(row)), split=row['labels']['split'])
    blobs[receipt_name]=json.dumps(receipt).encode();manifest[receipt_name]=d.digest(blobs[receipt_name])


class AdapterTests(unittest.TestCase):
    def test_full_synthetic_adapter(self):
        rows=d.adapt(*evidence());self.assertEqual(len(rows),30)
        self.assertEqual(len(d.training_rows(rows,d.PROFILES[0])),20)

    def test_pinned_bytes(self):
        b,m=evidence();b['batch-1/acceptance.json']+=b' '
        with self.assertRaises(ValueError):d.adapt(b,m)

    def test_receipt_cases_and_authority(self):
        for key,val in [('evaluation_authorized',True),('independent_review',True),
                        ('retention','temporary'),('cases',[]),('unexpected',1)]:
            b,m=evidence();mutate(b,m,'batch-1/acceptance.json',lambda a:a.update({key:val}))
            with self.assertRaises(ValueError):d.adapt(b,m)

    def test_rejected_case_wrong_hash_revision_or_split(self):
        for key,val in [('content_decision','reject'),('label_decision','uncertain'),
                        ('proposal_record_sha256','0'*64),('revision',True),('split','test')]:
            b,m=evidence();mutate(b,m,'batch-1/acceptance.json',lambda a:a['cases'][0].update({key:val}))
            with self.assertRaises(ValueError):d.adapt(b,m)

    def test_changed_content_even_repin_packet(self):
        b,m=evidence();mutate(b,m,'batch-1/reviewed-proposal.json',lambda a:a['records'][0].update(request='changed'))
        with self.assertRaises(ValueError):d.adapt(b,m)

    def test_malformed_bytes(self):
        for raw in [b'{"a":1,"a":2}',b'{"a":NaN}',b'x'*(d.MAX_BYTES+1)]:
            with self.assertRaises(ValueError):d.parse(raw)

    def test_label_privacy_and_prohibitions(self):
        for key,val in [('optional',['calendar']),('prohibited',[]),('split','test'),
                        ('required',['shell']),('optional',['timer'])]:
            row=fixture_row(0);row['labels'][key]=val
            with self.assertRaises(ValueError):d.label_check(row)

    def test_train_dev_input_separation(self):
        rows=d.adapt(*evidence());expected=d.training_rows(rows,d.PROFILES[1])
        for row in rows:
            if row['labels']['split']=='dev':row['labels']['required']=['web'];row['stratum']='changed'
        self.assertEqual(expected,d.training_rows(rows,d.PROFILES[1]))
        self.assertEqual(set(expected[0]),{'text','status','required'})
        row=rows[-1];text=d.input_text(row,d.PROFILES[1])
        row['labels']={'private':'secret-marker'}
        self.assertEqual(text,d.input_text(row,d.PROFILES[1]))
        self.assertNotIn('secret-marker',text)

    def test_profiles_and_empty_training(self):
        row=fixture_row(0)
        self.assertEqual(d.input_text(row,d.PROFILES[1]),row['request']+'\nSynthetic context:\n'+row['synthetic_context'])
        with self.assertRaises(ValueError):d.input_text(row,'new')
        with self.assertRaises(ValueError):d.training_rows([],d.PROFILES[0])

    def test_rebound_duplicate_family_and_cross_split_text(self):
        b,m=evidence();change_case(b,m,3,0,lambda row:row.update(family_id='fixture-00'))
        with self.assertRaises(ValueError):d.adapt(b,m)
        b,m=evidence();change_case(b,m,3,0,lambda row:row.update(request='[FIXTURE] timer example 0'))
        with self.assertRaises(ValueError):d.adapt(b,m)

    def test_rebound_revision_and_split(self):
        for change in (lambda row:row.update(revision=2),
                       lambda row:row['labels'].update(split='train'),
                       lambda row:row.update(stratum='not-a-class')):
            b,m=evidence();change_case(b,m,3,0,change)
            with self.assertRaises(ValueError):d.adapt(b,m)

    def test_effort_and_review_date_checks(self):
        b,m=evidence();mutate(b,m,'batch-1/effort.json',lambda a:a.update(minutes=True))
        with self.assertRaises(ValueError):d.adapt(b,m)
        b,m=evidence();mutate(b,m,'batch-1/effort.json',lambda a:a.update(extra='unknown'))
        with self.assertRaises(ValueError):d.adapt(b,m)
        b,m=evidence();mutate(b,m,'batch-1/acceptance.json',lambda a:a.update(recorded_at='2026-10-10T00:00:00+00:00'))
        with self.assertRaises(ValueError):d.adapt(b,m)

    def test_duplicate_number_and_bad_status(self):
        b,m=evidence();change_case(b,m,1,1,lambda row:row.update(number=1))
        with self.assertRaises(ValueError):d.adapt(b,m)
        b,m=evidence();change_case(b,m,1,1,lambda row:row['labels'].update(acceptable_statuses=['execute']))
        with self.assertRaises(ValueError):d.adapt(b,m)


class ScoreTests(unittest.TestCase):
    def prediction(self,status='plan',labels=None):
        return {'status':status,'labels':['timer'] if labels is None else labels,
                'authorization':'not-granted','confidence':None}

    def test_complete_and_missing(self):
        t=fixture_row(0)['labels']
        self.assertTrue(d.score(t,self.prediction())['complete'])
        self.assertEqual(d.score(t,self.prediction(labels=[]))['missing'],['timer'])
        self.assertEqual(d.score(t,self.prediction(labels=['timer','web']))['extra'],['web'])

    def test_nonplan_and_multiple_acceptable(self):
        t=fixture_row(0)['labels'];t.update(required=[],acceptable_statuses=['deny','unsupported'])
        self.assertTrue(d.score(t,self.prediction('deny',[]))['complete'])
        self.assertTrue(d.score(t,self.prediction('unsupported',[]))['covered'])
        self.assertFalse(d.score(t,self.prediction('deny',['timer']))['valid'])

    def test_malformed_kept_and_prohibited_counted(self):
        t=fixture_row(0)['labels']
        for p in [None,{},self.prediction(labels=['shell']),self.prediction(labels=['timer','timer'])]:
            self.assertFalse(d.score(t,p)['valid'])
        result=d.score(t,self.prediction(labels=['shell']))
        self.assertEqual(result['prohibited'],['shell'])
        stats=d.aggregate([result,d.score(t,self.prediction())])
        self.assertEqual(stats['families'],2);self.assertEqual(stats['complete_fraction'],.5)

    def test_zero_coverage_and_confidence(self):
        t=fixture_row(0)['labels'];a=d.score(t,self.prediction('abstain',[]))
        self.assertIsNone(d.aggregate([a])['covered_error_fraction'])
        p=self.prediction();p['confidence']=.9;self.assertFalse(d.score(t,p)['valid'])

    def test_disagreement_denominator(self):
        t=fixture_row(0)['labels']
        def row(p):return {'family_id':'fixture-a','prediction':p,'score':d.score(t,p)}
        result=d.disagreement([row(self.prediction()),row(None)],
                              [row(self.prediction('abstain',[])),row(self.prediction())])
        self.assertEqual(result,{'valid_pairs':1,'invalid_pairs':1,'disagreements':1,'fraction':1})

    def test_latency(self):
        self.assertEqual(d.latency([4,1,3,2]),{'count':4,'median_ns':2.5,'p95_ns':4})
        self.assertIsNone(d.latency([])['p95_ns'])

    def test_clarify_and_misaligned_families(self):
        t=fixture_row(0)['labels'];t.update(required=[],acceptable_statuses=['clarify'])
        prediction=self.prediction('clarify',[]);checked=d.score(t,prediction)
        self.assertTrue(checked['complete']);self.assertTrue(checked['covered'])
        a={'family_id':'fixture-a','prediction':prediction,'score':checked}
        b=dict(a,family_id='fixture-b')
        with self.assertRaises(ValueError):d.disagreement([a],[b])


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=r.load_engine_source(Path(__file__).with_name('routing_smoke.py'))

    def fixtures(self):
        rows=[fixture_row(0),fixture_row(1,'dev')]
        for row in rows:row['proposal_origin']='synthetic-evaluator-fixture'
        return rows

    def test_fixture_only_and_no_io(self):
        with patch.object(socket,'socket',side_effect=AssertionError('network')), \
             patch.object(subprocess,'Popen',side_effect=AssertionError('process')), \
             patch('builtins.open',side_effect=AssertionError('file access')):
            result=r.compare_fixtures(self.fixtures(),self.source)
        self.assertFalse(result['evaluation_authorized'])
        self.assertIsNone(result['privacy_routing_quality'])
        self.assertEqual(result['profiles'][d.PROFILES[0]]['engines']['existing-keyword-rules']['warm_latency']['count'],30)

    def test_accepted_corpus_is_disabled(self):
        rows=self.fixtures();rows[0]['proposal_origin']='ai-proposed-s0-draft'
        with self.assertRaises(ValueError):r.compare_fixtures(rows,self.source)
        with self.assertRaises(PermissionError):r.require_live_readiness(approved=True)

    def test_source_pin_and_no_default_evaluate(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.py';p.write_text('raise AssertionError()')
            with self.assertRaises(ValueError):r.load_engine_source(p)
        with patch.object(self.source,'evaluate',side_effect=AssertionError('wrong corpus')):
            r.compare_fixtures(self.fixtures(),self.source)

    def test_budget_keeps_missing_rows(self):
        result=r.compare_fixtures(self.fixtures(),self.source,rss=lambda:257)
        self.assertIsNotNone(result['stop_reason'])
        for p in result['profiles'].values():
            for engine in p['engines'].values():
                self.assertEqual(engine['metrics']['families'],1)
                self.assertEqual(engine['metrics']['invalid'],1)

    def test_engine_exception_stays_failure(self):
        with patch.object(self.source,'rules',side_effect=RuntimeError('sensitive message')):
            result=r.compare_fixtures(self.fixtures(),self.source)
        text=json.dumps(result);self.assertNotIn('sensitive message',text)
        engine=result['profiles'][d.PROFILES[0]]['engines']['existing-keyword-rules']
        self.assertEqual(engine['metrics']['invalid'],1)

    def test_fixed_ties_and_no_training_on_dev(self):
        rows=self.fixtures();other=copy.deepcopy(rows[0]);other['family_id']='fixture-zz'
        other['labels']['required']=['web'];rows.append(other)
        model=self.source.Nearest(d.training_rows(rows,d.PROFILES[0]))
        self.assertEqual(model.predict(rows[0]['request'],.2)['labels'],['timer'])
        self.assertEqual(len(model.training),2)

    def test_wall_unknown_rss_and_output_budget(self):
        ticks=iter(range(0,10**15,61*10**9))
        result=r.compare_fixtures(self.fixtures(),self.source,clock=lambda:next(ticks))
        self.assertIsNotNone(result['stop_reason'])
        with self.assertRaises(ValueError):
            # No output may serialize a nonfinite resource observation.
            r.compare_fixtures(self.fixtures(),self.source,rss=lambda:float('nan'))
        with patch.object(r,'MAX_OUTPUT',1):
            with self.assertRaises(ValueError):r.compare_fixtures(self.fixtures(),self.source)

    def test_full_fixture_pipeline_and_input_immutability(self):
        blobs,manifest=evidence();original=copy.deepcopy(blobs)
        rows=d.adapt(blobs,manifest)
        for row in rows:row['proposal_origin']='synthetic-evaluator-fixture'
        saved=copy.deepcopy(rows)
        result=r.compare_fixtures(rows,self.source)
        self.assertEqual(blobs,original);self.assertEqual(rows,saved)
        for profile in result['profiles'].values():
            for engine in profile['engines'].values():
                self.assertEqual(engine['metrics']['families'],10)
                self.assertEqual(engine['warm_latency']['count'],300)

    def test_interrupted_fixture_run_retains_every_denominator(self):
        rows=self.fixtures();other=fixture_row(2,'dev');other['proposal_origin']='synthetic-evaluator-fixture';rows.append(other)
        calls=[0]
        def clock():
            calls[0]+=1
            return 0 if calls[0]<14 else 61*10**9
        result=r.compare_fixtures(rows,self.source,clock=clock)
        self.assertIsNotNone(result['stop_reason'])
        for profile in result['profiles'].values():
            for engine in profile['engines'].values():
                self.assertEqual(engine['metrics']['families'],2)
                self.assertEqual([x['family_id'] for x in engine['rows']],['fixture-01','fixture-02'])


if __name__=='__main__':unittest.main()
