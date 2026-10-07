"""Source-local Authentik 2026.8 identity canary; metadata-only by default.

Run through ak shell only after approving this exact file. Set the shell global
ASTER_WORKER_AUTH_CANARY=True to create temporary objects and issue/revoke one
access token. Secrets stay in process memory; stdout contains booleans only.
This does not install a worker or exercise the Mac network path.
"""
import base64
import json
import secrets
from datetime import timedelta

from django.test import Client
from django.utils import timezone
from authentik.core.models import Application, User, Token
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping

SLUG = 'aster-codex-worker'
USERNAME = 'aster-codex-worker-mac'
PROVIDER = 'Aster Codex Worker Canary'
SCOPE_NAME = 'Aster Worker Canary Scope'
TOKEN_NAME = 'aster-worker-auth-canary'


def run(apply=False):
    absent = (not Application.objects.filter(slug=SLUG).exists()
              and not OAuth2Provider.objects.filter(client_id=SLUG).exists()
              and not OAuth2Provider.objects.filter(name=PROVIDER).exists()
              and not User.objects.filter(username=USERNAME).exists()
              and not ScopeMapping.objects.filter(name=SCOPE_NAME).exists()
              and not Token.objects.filter(identifier=TOKEN_NAME).exists())
    if not absent:
        raise RuntimeError('Candidate identity collision; no changes made')
    template = OAuth2Provider.objects.get(client_id='aster-companion')
    if not template.signing_key_id:
        raise RuntimeError('Signing key prerequisite missing')
    if not apply:
        print('ASTER_AUTH_CANARY='+json.dumps({'candidate_names_available': absent,
              'signing_key_available': True, 'applied': False}))
        return

    created = []
    checks = {}
    try:
        user = User.objects.create(username=USERNAME, name='Temporary Aster worker canary',
                                   type='service_account', is_active=True)
        created.append(user)
        scope = ScopeMapping.objects.create(name=SCOPE_NAME, scope_name='aster.worker',
                                             expression='return {}')
        created.append(scope)
        provider = OAuth2Provider.objects.create(name=PROVIDER, client_id=SLUG,
            client_type='confidential', client_secret=secrets.token_urlsafe(48),
            grant_types=['client_credentials'], access_token_validity='minutes=5',
            authorization_flow=template.authorization_flow,
            invalidation_flow=template.invalidation_flow, signing_key=template.signing_key,
            issuer_mode='per_provider', sub_mode='hashed_user_id')
        created.append(provider)
        provider.property_mappings.add(scope)
        app = Application.objects.create(slug=SLUG, name=PROVIDER, provider=provider)
        created.append(app)
        binding = PolicyBinding.objects.create(target=app, user=user, order=0,
                                               enabled=True, negate=False, timeout=30)
        created.append(binding)
        credential = Token.objects.create(identifier=TOKEN_NAME, user=user,
            intent='app_password', expiring=True, expires=timezone.now()+timedelta(minutes=10))
        created.append(credential)
        client = Client(raise_request_exception=False)
        def post(path, data, authorization=None):
            headers = {'HTTP_HOST': 'auth.elliottrook.com'}
            if authorization: headers['HTTP_AUTHORIZATION'] = authorization
            return client.post(path, data=data, secure=True, **headers)
        response = post('/application/o/token/', dict(grant_type='client_credentials',
            client_id=SLUG, username=USERNAME, password=credential.key, scope='aster.worker'))
        if response.status_code != 200:
            raise RuntimeError('Token issuance failed; response withheld')
        token = response.json().get('access_token')
        if not isinstance(token, str) or not token:
            raise RuntimeError('Access token missing; response withheld')
        basic = 'Basic '+base64.b64encode((SLUG+':'+provider.client_secret).encode()).decode()
        response = post('/application/o/introspect/', {'token': token}, basic)
        if response.status_code != 200:
            raise RuntimeError('Introspection failed; response withheld')
        claims = response.json()
        checks['active'] = claims.get('active') is True
        checks['issuer'] = claims.get('iss') == 'https://auth.elliottrook.com/application/o/aster-codex-worker/'
        checks['audience'] = claims.get('aud') in (SLUG, [SLUG])
        checks['client'] = claims.get('client_id') == SLUG
        checks['subject_present'] = isinstance(claims.get('sub'), str) and bool(claims['sub'])
        checks['scope'] = 'aster.worker' in claims.get('scope', '').split()
        checks['bounded_lifetime'] = (type(claims.get('iat')) is int and type(claims.get('exp')) is int
                                      and 0 < claims['exp']-claims['iat'] <= 300)
        response = post('/application/o/revoke/', {'token': token}, basic)
        checks['revocation_response'] = response.status_code == 200
        response = post('/application/o/introspect/', {'token': token}, basic)
        checks['revoked_denied'] = response.status_code == 200 and response.json().get('active') is False
        if not all(checks.values()):
            raise RuntimeError('Authentication contract mismatch')
    finally:
        # Only exact objects created by this invocation, never name-based deletion.
        cleanup_ok = True
        for obj in reversed(created):
            try:
                obj.delete()
            except Exception:
                cleanup_ok = False
        print('ASTER_AUTH_CANARY='+json.dumps({'applied': True, 'checks': checks,
                                               'temporary_objects_removed': cleanup_ok}))
        if not cleanup_ok:
            raise RuntimeError('Temporary identity cleanup requires operator recovery')


run(globals().get('ASTER_WORKER_AUTH_CANARY') is True)
