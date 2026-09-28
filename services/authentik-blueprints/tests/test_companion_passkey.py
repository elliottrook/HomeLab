import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion_passkey import companion_passkey_claims, PASSKEY_ACR, COMPANION_FLOW_PATH

class PasskeyClaimsTests(unittest.TestCase):
    def setUp(self):
        self.created=datetime.fromtimestamp(2000,timezone.utc)
        self.provider=NS(pk=26,client_id='aster-companion')
        self.user=NS(pk=42,is_active=True)
        self.token=NS(provider_id=26,user_id=42,session=NS(user_id=42),auth_time=self.created)
        self.event=NS(action='login',user={'pk':42},created=self.created,context={
            'auth_method':'auth_mfa','http_request':{'path':COMPANION_FLOW_PATH,'method':'POST'},
            'auth_method_args':{'mfa_devices':[{'app':'authentik_stages_authenticator_webauthn','model_name':'webauthndevice'}]}})
    def claims(self):
        return companion_passkey_claims(self.provider,self.token,self.user,self.event,1900,2100)
    def test_verified_session(self):
        self.assertEqual(self.claims(),{'acr':PASSKEY_ACR})
    def test_login_stage_get_continuation(self):
        self.event.context['http_request']['method']='GET'
        self.assertEqual(self.claims(),{'acr':PASSKEY_ACR})
    def test_refresh_preserves_old_auth_time(self):
        before=self.token.auth_time
        self.assertEqual(self.claims(),{'acr':PASSKEY_ACR})
        self.assertEqual(self.token.auth_time,before)
        self.token.auth_time=datetime.fromtimestamp(2100,timezone.utc)
        self.assertEqual(self.claims(),{})
    def test_generic_password_and_passwordless_labels_are_insufficient(self):
        for method in ['password','auth_webauthn_pwl','mfa',None]:
            self.event.context['auth_method']=method
            self.assertEqual(self.claims(),{})
    def test_wrong_device_class_or_malformed_evidence(self):
        args=self.event.context['auth_method_args']
        for devices in [None,[],{},['webauthn'],[{'app':'authentik_stages_authenticator_totp','model_name':'totpdevice'}],[{'app':'authentik_stages_authenticator_webauthn','model_name':'totpdevice'}]]:
            args['mfa_devices']=devices
            self.assertEqual(self.claims(),{})
    def test_device_enrollment_or_user_attributes_cannot_grant_assurance(self):
        self.user.attributes={'passkey':True,'acr':PASSKEY_ACR}
        self.event.context['auth_method_args']={'known_device':True}
        self.assertEqual(self.claims(),{})
    def test_other_session_user_and_token_user(self):
        self.token.session.user_id=43;self.assertEqual(self.claims(),{})
        self.token.session.user_id=42;self.token.user_id=43;self.assertEqual(self.claims(),{})
    def test_event_user_mismatch(self):
        self.event.user={'pk':43};self.assertEqual(self.claims(),{})
    def test_provider_mismatch(self):
        self.token.provider_id=25;self.assertEqual(self.claims(),{})
    def test_wrong_flow_or_method(self):
        self.event.context['http_request']['path']='/other/';self.assertEqual(self.claims(),{})
        self.event.context['http_request']['path']=COMPANION_FLOW_PATH
        self.event.context['http_request']['method']='HEAD';self.assertEqual(self.claims(),{})
    def test_delegation_and_user_switch(self):
        self.token.actor=NS();self.assertEqual(self.claims(),{})
        self.token.actor=None;self.event.context['is_user_switch']=True;self.assertEqual(self.claims(),{})
    def test_pre_policy_future_and_wrong_timestamp(self):
        for epoch in [1800,2200]:
            self.event.created=self.token.auth_time=datetime.fromtimestamp(epoch,timezone.utc)
            self.assertEqual(self.claims(),{})
        self.event.created=self.created;self.token.auth_time=self.created+timedelta(microseconds=1)
        self.assertEqual(self.claims(),{})
    def test_missing_session_event_and_inactive_user(self):
        self.event=None;self.assertEqual(self.claims(),{})
        self.setUp();self.token.session=None;self.assertEqual(self.claims(),{})
        self.setUp();self.user.is_active=False;self.assertEqual(self.claims(),{})
    def test_claim_contains_no_identity_or_timestamp(self):
        self.assertEqual(set(self.claims()),{'acr'})

if __name__=='__main__':unittest.main()
