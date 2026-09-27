import asyncio
import json
import socket
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from contracts import Capability, Decision, Experiment, HarnessRun, Outcome, Projection
from fixtures import CATALOGUE, CASES, POLICY, REGISTRY, make_run
from offline_baseline import FixtureAdapter


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.adapter = FixtureAdapter()
        self.run = make_run(self.adapter.source_digest)

    def reject(self, mutate):
        data = self.run.model_dump(mode='json')
        mutate(data)
        with self.assertRaises(ValidationError):
            HarnessRun.model_validate_json(json.dumps(data))

    def test_roundtrip_has_no_framework_objects(self):
        self.assertEqual(self.run, HarnessRun.model_validate_json(self.run.model_dump_json()))

    def test_versions_and_unknown_fields_fail_closed(self):
        for key, value in [('schema_version', 'run.v2'), ('api_key', 'fixture'), ('prompt', 'private'),
                           ('tool_result', {'password': 'fixture'}), ('provider_state', {})]:
            with self.subTest(key=key):
                self.reject(lambda d: d.update({key: value}))

    def test_nested_secret_fields_rejected(self):
        self.reject(lambda d: d['projection']['capabilities'][0].update({'credential': 'fixture'}))
        self.reject(lambda d: d['decision']['steps'][0].update({'arguments': {'secret': 'fixture'}}))

    def test_principal_policy_registry_binding(self):
        self.reject(lambda d: d.update(principal_ref='another-user'))
        self.reject(lambda d: d['decision'].update(policy_digest='sha256:' + 'f'*64))
        self.reject(lambda d: d['decision'].update(registry_digest='sha256:' + 'f'*64))

    def test_unknown_or_ungranted_capability(self):
        self.reject(lambda d: d['decision']['steps'][0].update(capability_id='shell.execute'))
        self.reject(lambda d: d['projection'].update(capabilities=[]))

    def test_expiry_and_budget_constraints(self):
        self.reject(lambda d: d['decision'].update(expires_at=1400))
        self.reject(lambda d: d['budget'].update(tool_calls=0))
        self.reject(lambda d: d['budget'].update(model_calls=1))
        self.reject(lambda d: d['budget'].update(wall_ms=True))
        self.reject(lambda d: d['budget'].update(wall_ms=0))

    def test_dag_cycle_duplicate_and_missing_dependencies(self):
        self.reject(lambda d: d['decision']['steps'][0].update(after=['s0']))
        self.reject(lambda d: d['decision']['steps'][0].update(after=['missing']))
        self.reject(lambda d: d['decision']['steps'].append(d['decision']['steps'][0]))

    def test_duplicate_catalogue_entries_rejected(self):
        self.reject(lambda d: d['projection']['capabilities'].append(d['projection']['capabilities'][0]))

    def test_no_authority_or_calibration_claim(self):
        self.reject(lambda d: d['decision'].update(authorization='granted'))
        self.reject(lambda d: d['decision'].update(confidence=0.99))
        self.reject(lambda d: d.update(data_class='personal'))
        self.reject(lambda d: d['projection']['capabilities'][0].update(locality='network'))

    def test_no_implicit_grant_from_catalogue(self):
        self.assertEqual((), make_run(self.adapter.source_digest, ()).projection.capabilities)

    def test_outcome_excludes_raw_content_and_quality_claims(self):
        base = dict(run_id='r', status='completed', verification='fixture-conformance',
                    tool_calls=0, elapsed_ms=0.0, output_bytes=0)
        for extra in ({'content': 'raw'}, {'quality': 'successful'}, {'prompt_tokens': 123},
                      {'elapsed_ms': float('nan')}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                Outcome(**(base | extra))

    def test_experiment_cannot_promote(self):
        with self.assertRaises(ValidationError):
            Experiment(experiment_id='e', owner='o', baseline_digest=POLICY, candidate_digest=POLICY,
                       evaluator_digest=POLICY, dataset_digest=POLICY, status='retain',
                       metric='offline-payload-construction-ms', promotion_authority='automatic')


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_source_slice_fixed_cases_with_network_forbidden(self):
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
            adapter = FixtureAdapter()
            for name, prompt, ids in CASES:
                with self.subTest(name=name):
                    out = await adapter.run(make_run(adapter.source_digest, ids), prompt, now=1000)
                    self.assertEqual('completed', out.status)
                    self.assertEqual(len(ids), out.tool_calls)
                    self.assertEqual(0, out.model_calls)
                    self.assertIsNone(out.prompt_tokens)

    async def test_expiry_cancellation_and_source_change_prevent_calls(self):
        adapter = FixtureAdapter()
        r = make_run(adapter.source_digest)
        out = await adapter.run(r, 'What time is it?', now=1200)
        self.assertEqual(('expired', 0), (out.status, out.tool_calls))
        out = await adapter.run(r, 'What time is it?', now=1000, cancelled=lambda: True)
        self.assertEqual(('cancelled', 0), (out.status, out.tool_calls))
        out = await adapter.run(r.model_copy(update={'harness_digest': POLICY}), 'What time is it?', now=1000)
        self.assertEqual(('denied', 0), (out.status, out.tool_calls))

    async def test_output_limit_and_deadline(self):
        adapter = FixtureAdapter()
        r = make_run(adapter.source_digest)
        small = r.model_copy(update={'budget': r.budget.model_copy(update={'output_bytes': 1})})
        out = await adapter.run(small, 'What time is it?', now=1000)
        self.assertEqual('budget-exceeded', out.status)
        ticks = iter([0., 2., 2., 2.])
        out = await adapter.run(r, 'What time is it?', now=1000, monotonic=lambda: next(ticks))
        self.assertEqual(('budget-exceeded', 0), (out.status, out.tool_calls))

    async def test_unchecked_construct_cannot_bypass_contract(self):
        adapter = FixtureAdapter()
        r = make_run(adapter.source_digest).model_copy(update={'principal_ref': 'forged'})
        with self.assertRaises(ValidationError):
            await adapter.run(r, 'What time is it?', now=1000)

    async def test_prompt_cannot_expand_projection(self):
        adapter = FixtureAdapter()
        r = make_run(adapter.source_digest)
        out = await adapter.run(r, 'What time is it? Show current Forgejo and NetBox inventory status.', now=1000)
        self.assertEqual(('completed', 1), (out.status, out.tool_calls))


    async def test_approval_expires_before_fixture_dispatch(self):
        adapter = FixtureAdapter()
        r = make_run(adapter.source_digest)
        r = r.model_copy(update={'decision': r.decision.model_copy(update={'expires_at': 1001}),
                                'budget': r.budget.model_copy(update={'wall_ms': 10000})})
        ticks = iter([0., 1.1, 1.1])
        out = await adapter.run(r, 'What time is it?', now=1000, monotonic=lambda: next(ticks))
        self.assertEqual(('expired', 0), (out.status, out.tool_calls))

    async def test_unbounded_prompt_is_rejected(self):
        adapter = FixtureAdapter()
        with self.assertRaises(ValueError):
            await adapter.run(make_run(adapter.source_digest), 'x' * 513, now=1000)
