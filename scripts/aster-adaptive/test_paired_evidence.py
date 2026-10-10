import copy
import unittest
from evidence_store import digest
from paired_evidence import aggregate


class PairedTests(unittest.TestCase):
    def setUp(self):
        self.events=[]
        def event(kind,record):
            h=digest({'kind':kind,'record':record,'index':len(self.events)})
            self.events.append(dict(kind=kind,record=record,event_digest=h))
            return h
        self.event=event
        dataset=dict(cases=[dict(case_id=c,family_id='shared-family',
            expected_digest=digest({'status':'completed','tool_calls':1})) for c in ('a','b')])
        event('dataset',dataset)
        event('experiment',dict(experiment_id='e',dataset_digest=digest(dataset)))
        h=event('paired-plan',dict(experiment_id='e',repetitions=2,maximum_p95_delta_ms=5.0))
        self.record=dict(experiment_id='e',plan_event_digest=h,pairs=[])
        for case in ('a','b'):
            for i in range(2):
                pair=dict(case_id=case,repetition=i)
                for role in ('baseline','candidate'):
                    r=event('run',dict(case_id=case,candidate_role=role,run=dict(experiment_id='e')))
                    pair[role+'_outcome']=event('linked-outcome',dict(experiment_id='e',run_event_digest=r,
                        outcome=dict(status='completed',tool_calls=1,verification='fixture-conformance',elapsed_ms=1.0)))
                self.record['pairs'].append(pair)

    def test_family_denominator_not_repetitions_or_cases(self):
        totals,_=aggregate(self.record,self.events,digest)
        self.assertEqual(dict(family_count=1,passed_families=1,verdict='pass'),totals)

    def test_omitted_pair_reused_outcome_and_wrong_role_denied(self):
        variants=[]
        a=copy.deepcopy(self.record); a['pairs'].pop(); variants.append(a)
        a=copy.deepcopy(self.record); a['pairs'][1]['candidate_outcome']=a['pairs'][0]['candidate_outcome']; variants.append(a)
        a=copy.deepcopy(self.record); a['pairs'][0]['candidate_outcome']=a['pairs'][0]['baseline_outcome']; variants.append(a)
        for variant in variants:
            with self.assertRaises(ValueError):
                aggregate(variant,self.events,digest)

    def test_wrong_case_and_experiment_denied(self):
        for field,value in (('case_id','other'),('run',dict(experiment_id='other'))):
            events=copy.deepcopy(self.events)
            next(e for e in events if e['kind']=='run')['record'][field]=value
            with self.assertRaises(ValueError):
                aggregate(self.record,events,digest)

    def test_failure_or_slow_case_fails_whole_family(self):
        for field,value in (('status','failed'),('elapsed_ms',100.0)):
            events=copy.deepcopy(self.events)
            h=self.record['pairs'][0]['candidate_outcome']
            next(e for e in events if e['event_digest']==h)['record']['outcome'][field]=value
            totals,_=aggregate(self.record,events,digest)
            self.assertEqual(dict(family_count=1,passed_families=0,verdict='fail'),totals)

    def test_cherry_picked_extra_record_denied(self):
        self.event('linked-outcome',dict(experiment_id='e'))
        with self.assertRaisesRegex(ValueError,'omitted'):
            aggregate(self.record,self.events,digest)


class PairedStoreTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from evidence_store import Dataset, EvidenceStore
        from fixtures import make_run
        from test_evidence_store import D, experiment
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=EvidenceStore(Path(self.temp.name)/'paired.db')
        self.addCleanup(self.store.close)
        data=Dataset(dataset_id='paired-test',cases=(dict(case_id='a',family_id='family',
            input_digest=D,expected_digest=digest({'status':'completed','tool_calls':1})),)).model_dump(mode='json')
        self.store.append('dataset','dataset',data)
        spec=experiment() | {'dataset_digest':digest(data)}
        self.store.append('spec','experiment',spec)
        self.experiment_id=spec['experiment_id']
        plan=self.store.append('plan','paired-plan',dict(experiment_id=self.experiment_id,
            repetitions=2,warmups=0,maximum_p95_delta_ms=5.0))
        pairs=[]
        for i in range(2):
            pair=dict(case_id='a',repetition=i)
            for role in ('baseline','candidate'):
                run=make_run(D).model_dump(mode='json')
                run.update(run_id=f'{role}-{i}',experiment_id=self.experiment_id)
                self.registered=dict(dataset_digest=digest(data),case_id='a',candidate_role=role,run=run)
                rh=self.store.append('run-'+run['run_id'],'run',self.registered)
                pair[role+'_outcome']=self.store.append('out-'+run['run_id'],'linked-outcome',dict(
                    experiment_id=self.experiment_id,run_event_digest=rh,outcome=dict(
                        run_id=run['run_id'],status='completed',verification='fixture-conformance',
                        tool_calls=1,elapsed_ms=1.0,output_bytes=100)))
            pairs.append(pair)
        self.record=dict(experiment_id=self.experiment_id,plan_event_digest=plan,pairs=pairs,
                         family_count=1,passed_families=1,verdict='pass')

    def test_fabricated_totals_and_late_plan_rejected(self):
        with self.assertRaisesRegex(ValueError,'totals'):
            self.store.append('eval','paired-evaluation',self.record | {'family_count':4})
        with self.assertRaises(ValueError):
            self.store.append('plan2','paired-plan',dict(experiment_id=self.experiment_id,
                repetitions=2,warmups=0,maximum_p95_delta_ms=5.0))
        self.assertEqual([],self.store.records('paired-evaluation'))

    def test_finalized_evaluation_blocks_new_runs_and_accepts_bound_review(self):
        h=self.store.append('eval','paired-evaluation',self.record)
        self.assertEqual(h,self.store.append('eval','paired-evaluation',self.record))
        with self.assertRaisesRegex(ValueError,'finalized'):
            self.store.append('late-run','run',self.registered | {'run':self.registered['run'] | {'run_id':'late'}})
        with self.assertRaises(ValueError):
            self.store.append('eval2','paired-evaluation',self.record)
        self.store.append('review','review',dict(experiment_id=self.experiment_id,evaluation_digest=h,
            reviewer_ref='synthetic-reviewer',decision='request-more-evidence',reason='insufficient-evidence'))
        self.store.verify()
