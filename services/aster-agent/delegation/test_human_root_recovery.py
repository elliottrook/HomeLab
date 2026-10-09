import unittest
import human_root_recovery as recovery


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.revoked=set();self.changed=False;self.timeout=False
        self.records={key:{'accessor':key,'policies':['root'],'path':'auth/token/root',
            'display_name':'root','creation_time':100,'orphan':True,'type':'service','id':''}
            for key in ('own','lost','unrelated')}

    def api(self,token,method,path,payload=None):
        self.calls.append((method,path,payload))
        if path=='auth/token/lookup-self': return 200,{'data':self.records['own']}
        if path=='auth/token/accessors':
            return 200,{'data':{'keys':[k for k in self.records if k not in self.revoked]}}
        if path=='auth/token/lookup-accessor':
            return 200,{'data':dict(self.records[payload['accessor']])}
        if path=='auth/token/revoke-accessor':
            self.revoked.add(payload['accessor'])
            if self.timeout: raise TimeoutError('fixture')
            return 204,{}
        if path=='auth/token/revoke-self': self.revoked.add('own');return 204,{}
        self.fail('Unexpected API operation')

    def test_exact_selection_preserves_unrelated(self):
        result=recovery.recover(self.api,'fixture',lambda rows:'REVOKE lost')
        self.assertTrue(result['target_revoked'])
        self.assertEqual(self.revoked,{'lost','own'})

    def test_self_unknown_blank_and_fuzzy_selection_rejected(self):
        for selection in ('REVOKE own','REVOKE absent','','lost','REVOKE los'):
            with self.subTest(selection=selection):
                self.setUp()
                with self.assertRaises(ValueError):
                    recovery.recover(self.api,'fixture',lambda _:selection)
                self.assertEqual(self.revoked,{'own'})

    def test_changed_metadata_stops_target_mutation(self):
        def choose(rows):
            self.records['lost']['creation_time']=101
            return 'REVOKE lost'
        with self.assertRaises(ValueError): recovery.recover(self.api,'fixture',choose)
        self.assertEqual(self.revoked,{'own'})

    def test_unexpected_token_id_never_reaches_display(self):
        self.records['lost']['id']='fictional-secret'
        with self.assertRaises(ValueError):
            recovery.recover(self.api,'fixture',lambda _:self.fail('Should not display'))
        self.assertEqual(self.revoked,{'own'})

    def test_lost_revoke_response_is_not_retried(self):
        self.timeout=True
        with self.assertRaises(TimeoutError):
            recovery.recover(self.api,'fixture',lambda _:'REVOKE lost')
        self.assertEqual(sum(p=='auth/token/revoke-accessor' for _,p,_ in self.calls),1)
        self.assertIn('own',self.revoked)

    def test_non_root_and_non_generated_tokens_not_offered(self):
        self.records['lost']['policies']=['default']
        self.records['unrelated']['path']='auth/token/create'
        result=recovery.recover(self.api,'fixture',lambda _:self.fail('No candidates'))
        self.assertEqual(result,{'candidate_count':0,'target_revoked':False})
        self.assertEqual(self.revoked,{'own'})

    def test_interruption_retires_fresh_recovery_root(self):
        def choose(_): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): recovery.recover(self.api,'fixture',choose)
        self.assertEqual(self.revoked,{'own'})
