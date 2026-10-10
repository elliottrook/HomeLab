"""Frozen paired protocols and deterministic aggregation of linked evidence."""
import math
from typing import Annotated, Literal
from pydantic import Field
from contracts import Contract, Digest, Ref


class PairedPlan(Contract):
    schema_version: Literal['paired-plan.v1'] = 'paired-plan.v1'
    experiment_id: Ref
    repetitions: Annotated[int, Field(ge=2, le=100)]
    warmups: Annotated[int, Field(ge=0, le=20)]
    maximum_p95_delta_ms: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
    interpretation: Literal['synthetic-overhead-guardrail-only'] = 'synthetic-overhead-guardrail-only'


class Pair(Contract):
    case_id: Ref
    repetition: Annotated[int, Field(ge=0, le=99)]
    baseline_outcome: Digest
    candidate_outcome: Digest


class PairedEvaluation(Contract):
    schema_version: Literal['paired-evaluation.v1'] = 'paired-evaluation.v1'
    experiment_id: Ref
    plan_event_digest: Digest
    pairs: Annotated[tuple[Pair, ...], Field(min_length=1, max_length=4000)]
    family_count: Annotated[int, Field(ge=1)]
    passed_families: Annotated[int, Field(ge=0)]
    verdict: Literal['pass', 'fail']
    quality: Literal['not-evaluated'] = 'not-evaluated'
    promotion_authority: Literal['none'] = 'none'


def aggregate(record, prior, content_digest):
    """Derive totals; reject omitted cases, reused evidence and wrong provenance."""
    events = {p['event_digest']:p for p in prior}
    plan_event = events.get(record['plan_event_digest'])
    if not plan_event or plan_event['kind']!='paired-plan':
        raise ValueError('evaluation needs exact paired plan')
    plan = plan_event['record']
    if plan['experiment_id']!=record['experiment_id']:
        raise ValueError('paired experiment mismatch')
    specs = [p['record'] for p in prior if p['kind']=='experiment'
             and p['record']['experiment_id']==record['experiment_id']]
    if len(specs)!=1:
        raise ValueError('missing paired experiment')
    datasets = [p['record'] for p in prior if p['kind']=='dataset'
                and content_digest(p['record'])==specs[0]['dataset_digest']]
    if len(datasets)!=1:
        raise ValueError('missing paired dataset')
    cases = {c['case_id']:c for c in datasets[0]['cases']}
    expected = {(case,i) for case in cases for i in range(plan['repetitions'])}
    seen, used = set(), set()
    values = {case:{'baseline':[], 'candidate':[], 'conform':True} for case in cases}
    for pair in record['pairs']:
        key = pair['case_id'],pair['repetition']
        if key not in expected or key in seen:
            raise ValueError('duplicate or unexpected pair')
        seen.add(key)
        for role in ('baseline','candidate'):
            h = pair[role+'_outcome']
            event = events.get(h)
            if h in used or not event or event['kind']!='linked-outcome':
                raise ValueError('missing or reused paired outcome')
            used.add(h)
            linked = event['record']
            run_event = events.get(linked['run_event_digest'])
            if not run_event or run_event['kind']!='run':
                raise ValueError('missing paired run')
            run = run_event['record']
            if (linked['experiment_id']!=record['experiment_id'] or
                run['run']['experiment_id']!=record['experiment_id'] or
                run['case_id']!=pair['case_id'] or run['candidate_role']!=role):
                raise ValueError('paired run provenance mismatch')
            out = linked['outcome']
            value = values[pair['case_id']]
            value[role].append(out['elapsed_ms'])
            value['conform'] &= (out['verification']=='fixture-conformance' and
                content_digest({'status':out['status'],'tool_calls':out['tool_calls']})==cases[pair['case_id']]['expected_digest'])
    if seen!=expected:
        raise ValueError('incomplete paired coverage')
    available = {p['event_digest'] for p in prior if p['kind']=='linked-outcome'
                 and p['record']['experiment_id']==record['experiment_id']}
    if available!=used:
        raise ValueError('evaluation omitted recorded outcomes')
    families = {}
    details = {}
    for case,value in values.items():
        p95 = {role:sorted(value[role])[math.ceil(.95*len(value[role]))-1]
               for role in ('baseline','candidate')}
        delta = p95['candidate']-p95['baseline']
        passed = value['conform'] and delta<=plan['maximum_p95_delta_ms']
        family = cases[case]['family_id']
        families[family] = families.get(family,True) and passed
        details[case] = dict(p95_ms=p95, delta_ms=delta, passed=passed)
    return dict(family_count=len(families),passed_families=sum(families.values()),
                verdict='pass' if all(families.values()) else 'fail'), details
