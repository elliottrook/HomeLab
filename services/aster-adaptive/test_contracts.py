import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError
from baseline import BaselineSelector
from contracts import CONTRACTS, Decision, DecisionRequest, HarnessRun, Outcome, Step, validate_proposal
from evaluate import SOURCE, catalogue, request, run


class ContractsTests(unittest.TestCase):
    def setUp(self):
        self.selector=BaselineSelector(SOURCE,hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.catalogue=catalogue(self.selector)
        self.request=request({'id':'fixture'},self.catalogue)
        self.decision=self.selector.propose(self.request,self.catalogue,[{'role':'user','content':'What is the current time?'}],allowed=self.selector.names,now=10)

    def test_exported_schemas_match_candidate(self):
        root=Path(__file__).resolve().parents[2]
        for cls in CONTRACTS:
            expected=cls.model_json_schema();expected['$schema']='https://json-schema.org/draft/2020-12/schema'
            self.assertEqual(json.loads((root/'schemas/aster'/f'{cls.__name__}.v1.json').read_text()),expected)

    def test_fixture_conformance(self):
        self.assertEqual(run(repeats=1)['fixture_count'],12)

    def test_no_network_or_tools(self):
        with patch('socket.socket',side_effect=AssertionError('network forbidden')),patch('subprocess.Popen',side_effect=AssertionError('process forbidden')):
            self.assertEqual(run(repeats=1)['fixture_count'],12)

    def test_source_drift_denied(self):
        with self.assertRaises(ValueError):BaselineSelector(SOURCE,'0'*64)

    def test_baseline_module_initializers_not_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'source.py';p.write_text("raise RuntimeError('must not run')\n"+SOURCE.read_text())
            extracted=BaselineSelector(p,hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertTrue(extracted.select([{'role':'user','content':'time'}]))

    def test_unknown_schema_rejected(self):
        with self.assertRaises(ValidationError):Decision.model_validate(self.decision.model_dump() | {'schema_version':'decision.v9'})

    def test_secret_and_prompt_fields_rejected(self):
        for key in ('prompt','token','credential','chain_of_thought','principal'):
            with self.subTest(key=key),self.assertRaises(ValidationError):Decision.model_validate(self.decision.model_dump() | {key:'synthetic-secret'})

    def test_calibration_cannot_be_invented(self):
        with self.assertRaises(ValidationError):Decision.model_validate(self.decision.model_dump() | {'probability':.9})

    def test_authorization_cannot_be_granted(self):
        with self.assertRaises(ValidationError):Decision.model_validate(self.decision.model_dump() | {'authorization':'granted'})

    def test_strict_request_budget(self):
        for value in ('100',True,0,5001):
            with self.subTest(value=value),self.assertRaises(ValidationError):DecisionRequest.model_validate(self.request.model_dump() | {'deadline_ms':value})

    def test_cycles_and_forward_references_denied(self):
        for after in (['step-0'],['missing']):
            data=self.decision.model_dump();data['steps'][0]['after']=after
            with self.assertRaises(ValidationError):Decision.model_validate(data)

    def test_duplicate_steps_denied(self):
        data=self.decision.model_dump();data['steps']*=2
        with self.assertRaises(ValidationError):Decision.model_validate(data)

    def test_nonplan_cannot_carry_execution_plan(self):
        with self.assertRaises(ValidationError):Decision.model_validate(self.decision.model_dump() | {'status':'deny'})

    def test_expired_proposal_rejected(self):
        with self.assertRaises(ValueError):validate_proposal(self.request,self.decision,self.catalogue,now=40)

    def test_policy_mismatch_rejected(self):
        req=DecisionRequest.model_validate(self.request.model_dump() | {'policy_digest':'0'*64})
        with self.assertRaises(ValueError):validate_proposal(req,self.decision,self.catalogue,now=10)

    def test_stale_registry_rejected(self):
        req=DecisionRequest.model_validate(self.request.model_dump() | {'registry_digest':'0'*64})
        result=self.selector.propose(req,self.catalogue,[],allowed=self.selector.names,now=10)
        self.assertEqual(result.status,'deny')
        with self.assertRaises(ValueError):validate_proposal(req,result,self.catalogue,now=10)

    def test_catalogue_from_other_baseline_rejected(self):
        cat=self.catalogue.model_copy(update={'source_digest':'0'*64});req=request({'id':'fixture'},cat)
        result=self.selector.propose(req,cat,[],allowed=self.selector.names,now=10)
        self.assertEqual(result.status,'deny')

    def test_unknown_capability_rejected(self):
        data=self.decision.model_dump();data['steps'][0]['capability_id']='shell.execute'
        with self.assertRaises(ValueError):validate_proposal(self.request,Decision.model_validate(data),self.catalogue,now=10)

    def test_missing_catalogue_entry_denies_selector(self):
        cat=self.catalogue.model_copy(update={'capabilities':[]});req=request({'id':'fixture'},cat)
        decision=self.selector.propose(req,cat,[{'role':'user','content':'time'}],allowed=self.selector.names,now=10)
        self.assertEqual(decision.status,'deny');self.assertEqual(decision.steps,[])

    def test_allowlist_empty_never_expands_scope(self):
        result=self.selector.propose(self.request,self.catalogue,[{'role':'user','content':'time'}],allowed=frozenset(),now=10)
        self.assertEqual(result.status,'abstain')

    def test_deadline_abstention(self):
        with patch('baseline.time.monotonic_ns',side_effect=[0,6_000_000_000]):
            result=self.selector.propose(self.request,self.catalogue,[],allowed=self.selector.names,now=10)
        self.assertEqual(result.status,'degraded')

    def test_oversized_or_nested_input_rejected(self):
        for messages in ([{'role':'user','content':'x'*4097}], [{'role':'user','content':{'secret':'value'}}], [{'role':'user','content':'x','token':'x'}]):
            with self.assertRaises(ValueError):self.selector.propose(self.request,self.catalogue,messages,allowed=self.selector.names,now=10)

    def test_plan_budget_blocks_extra_steps(self):
        req=DecisionRequest.model_validate(self.request.model_dump() | {'max_steps':1})
        result=self.selector.propose(req,self.catalogue,[{'role':'user','content':'current homelab service status'}],allowed=self.selector.names,now=10)
        self.assertEqual(result.status,'abstain')
        self.assertEqual(result.reason_codes,['STEP_BUDGET_EXCEEDED'])

    def test_no_live_calls_claim(self):
        row=run(repeats=1)['results'][0]['run']
        with self.assertRaises(ValidationError):HarnessRun.model_validate(row | {'tool_calls':1})

    def test_no_false_execution_success(self):
        with self.assertRaises(ValidationError):Outcome(run_id='fixture',result='success',execution='succeeded',label_source='synthetic_expectation',route_correct=True)


if __name__=='__main__':unittest.main()
