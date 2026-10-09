import unittest
import admin_contract
from isolated_vault_rehearsal import diagnostic_event
from vault_provision import ROLE_PATH


class DiagnosticTests(unittest.TestCase):
    def test_api_body_and_unknown_path_never_escape(self):
        secret='fictional-private-marker'
        event=diagnostic_event('POST','auth/token/create-orphan',200,
            {'auth':{'client_token':secret},'errors':[secret]})
        self.assertNotIn(secret,str(event))
        self.assertEqual(diagnostic_event('GET',secret,403,{}),{'operation':'unrecognized'})

    def test_role_mismatch_reports_only_known_field_name(self):
        data={k:({'24h':86400,'5m':300}[v] if k.endswith('_ttl') else v)
              for k,v in admin_contract.role_request().items()}
        data['token_type']='fictional-private-marker'
        event=diagnostic_event('GET',ROLE_PATH,200,{'data':data})
        self.assertEqual(event['mismatched_fields'],['token_type'])
        self.assertNotIn('fictional-private-marker',str(event))
