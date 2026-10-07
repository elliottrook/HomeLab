import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs

import httpx
from credentials import (CredentialUnavailable, IntrospectionCredential,
                         KEYCHAIN_ACCOUNT, KEYCHAIN_SERVICE, POLICY,
                         WorkerToken, read_approle)


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'approle'
        self.path.write_text(json.dumps({'role_id':'fixture-role','secret_id':'fixture-secret'}))
        self.path.chmod(0o600)
        self.calls = []
        self.read_status, self.revoke_status = 200, 204
        self.policies = [POLICY]
        self.token_result = dict(access_token='fixture-access', token_type='Bearer',
                                 expires_in=300, scope='aster.worker')

    def tearDown(self): self.tmp.cleanup()

    def vault(self, request):
        self.calls.append((request.method, request.url.path))
        self.assertEqual(request.url.host, '192.168.50.24')
        if request.url.path.endswith('/login'):
            self.assertEqual(json.loads(request.content),
                             {'role_id':'fixture-role','secret_id':'fixture-secret'})
            return httpx.Response(200, json={'auth':{'client_token':'fixture-vault',
                'policies':self.policies,'lease_duration':300}})
        self.assertEqual(request.headers['X-Vault-Token'], 'fixture-vault')
        if request.url.path.endswith('/revoke-self'):
            return httpx.Response(self.revoke_status)
        self.assertEqual(request.url.path, '/v1/secret/data/ai-pam/aster-worker-introspection')
        return httpx.Response(self.read_status, json={'data':{'data':{'client_secret':'fixture-introspection'}}})

    def provider(self):
        return IntrospectionCredential(self.path, None, enabled=True,
                                       transport=httpx.MockTransport(self.vault))

    def test_disabled_never_reads_custody(self):
        with patch('credentials.read_approle') as reader, patch('credentials.subprocess.run') as keychain:
            for provider in (IntrospectionCredential('missing','missing'), WorkerToken()):
                with self.assertRaises(CredentialUnavailable): provider()
            reader.assert_not_called(); keychain.assert_not_called()

    def test_exact_vault_path_and_ephemeral_token_revocation(self):
        self.assertEqual(self.provider()(), 'fixture-introspection')
        self.assertEqual(self.calls, [('POST','/v1/auth/approle/login'),
            ('GET','/v1/secret/data/ai-pam/aster-worker-introspection'),
            ('POST','/v1/auth/token/revoke-self')])

    def test_read_failure_or_excess_authority_still_revokes(self):
        for status, policies in ((403,[POLICY]), (200,[POLICY,'default'])):
            self.calls=[]; self.read_status=status; self.policies=policies
            with self.assertRaises(CredentialUnavailable): self.provider()()
            self.assertEqual(self.calls[-1][1], '/v1/auth/token/revoke-self')
            if len(policies)>1: self.assertEqual(len(self.calls), 2)

    def test_revoke_failure_does_not_release_credential(self):
        self.revoke_status=503
        with self.assertRaises(CredentialUnavailable) as caught: self.provider()()
        self.assertEqual(str(caught.exception), 'Gateway credential unavailable')

    def test_unsafe_files_refused(self):
        self.path.chmod(0o644)
        with self.assertRaises(ValueError): read_approle(self.path)
        self.path.chmod(0o600)
        link=Path(self.tmp.name)/'link'; link.symlink_to(self.path)
        with self.assertRaises(OSError): read_approle(link)
        link.unlink(); os.link(self.path, link)
        with self.assertRaises(ValueError): read_approle(self.path)

    def token_endpoint(self, request):
        self.assertEqual(str(request.url), 'https://auth.elliottrook.com/application/o/token/')
        self.assertEqual(parse_qs(request.content.decode()), {
            'grant_type':['client_credentials'], 'client_id':['aster-codex-worker'],
            'username':['aster-codex-worker-mac'], 'password':['fixture-password'],
            'scope':['aster.worker']})
        return httpx.Response(200,json=self.token_result)

    def test_fixed_keychain_item_and_bounded_token(self):
        with patch('credentials.subprocess.run', return_value=subprocess.CompletedProcess([],0,b'fixture-password\n')) as run:
            token=WorkerToken(enabled=True,transport=httpx.MockTransport(self.token_endpoint))()
        self.assertEqual(token,'fixture-access')
        self.assertEqual(run.call_args.args[0], ['/usr/bin/security','find-generic-password',
            '-s',KEYCHAIN_SERVICE,'-a',KEYCHAIN_ACCOUNT,'-w'])
        self.assertEqual(run.call_args.kwargs['stderr'], subprocess.DEVNULL)
        self.assertNotIn('fixture-password', str(run.call_args))

    def test_token_boundary_and_custody_failures_are_sanitized(self):
        with patch('credentials.subprocess.run', return_value=subprocess.CompletedProcess([],0,b'fixture-password\n')):
            for key,value in [('expires_in',301),('expires_in',True),('scope','openid'),
                              ('refresh_token','unexpected'),('access_token','two words')]:
                previous=dict(self.token_result);self.token_result[key]=value
                with self.assertRaises(CredentialUnavailable):
                    WorkerToken(enabled=True,transport=httpx.MockTransport(self.token_endpoint))()
                self.token_result=previous
        with patch('credentials.subprocess.run', side_effect=RuntimeError('private material')):
            with self.assertRaises(CredentialUnavailable) as caught: WorkerToken(enabled=True)()
        self.assertNotIn('private',str(caught.exception))

    def test_redirect_or_oversized_response_denies_without_following(self):
        for response in (httpx.Response(302,headers={'Location':'https://elsewhere.invalid'}),
                         httpx.Response(200,content=b'x'*32769)):
            with patch('credentials.subprocess.run', return_value=subprocess.CompletedProcess([],0,b'fixture-password\n')):
                calls=[]
                def upstream(request): calls.append(request); return response
                with self.assertRaises(CredentialUnavailable):
                    WorkerToken(enabled=True,transport=httpx.MockTransport(upstream))()
                self.assertEqual(len(calls),1)
