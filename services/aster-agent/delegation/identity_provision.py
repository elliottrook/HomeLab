"""Source-local Authentik provisioning candidate; no automatic execution.

Creates only a new INACTIVE worker identity. Never activates it or logs secrets.
Use through a reviewed private delivery controller after deployment approval.
"""
import hashlib
import json
from pathlib import Path

SLUG='aster-codex-worker'
USER='aster-codex-worker-mac'
NAME='Aster Codex Worker'
SCOPE='Aster Codex Worker Scope'
TOKEN='aster-codex-worker-pilot'


def fingerprint():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def check_existing_access(rows):
    """Conservative precondition, not a universal Authentik policy evaluator.

    A new distinct user cannot match an existing positive user-only binding.
    More complex policies require review, never a guessed safe interpretation.
    """
    for row in rows:
        bindings=row['bindings']
        if (len(bindings)!=1 or bindings[0] != {
                'user':True,'group':False,'policy':False,'negate':False}):
            raise ValueError('Existing application access needs review')


def preflight():
    from authentik.core.models import Application, User, Token
    from authentik.policies.models import PolicyBinding
    from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
    if (Application.objects.filter(slug=SLUG).exists() or
            User.objects.filter(username=USER).exists() or
            Token.objects.filter(identifier=TOKEN).exists() or
            OAuth2Provider.objects.filter(client_id=SLUG).exists() or
            OAuth2Provider.objects.filter(name=NAME).exists() or
            ScopeMapping.objects.filter(name=SCOPE).exists()):
        raise ValueError('Provisioning names already exist; reconcile without retry')
    rows=[]
    for provider in OAuth2Provider.objects.all():
        if not set(provider.grant_types)&{'client_credentials','password'}: continue
        app=Application.objects.filter(provider=provider).first()
        if app is None: continue  # Installed grant code denies providers without apps.
        rows.append({'bindings':[{'user':b.user_id is not None,
            'group':b.group_id is not None,'policy':b.policy_id is not None,
            'negate':b.negate} for b in PolicyBinding.objects.filter(target=app,enabled=True)]})
    check_existing_access(rows)
    template=OAuth2Provider.objects.get(client_id='aster-companion')
    if not template.signing_key_id: raise ValueError('Signing prerequisite missing')
    return template, len(rows)


class IdentityProvisioningIncomplete(Exception):
    def __init__(self, record):
        self.record=record
        super().__init__('Worker remains inactive; reconcile custody before proceeding')


def provision(deliver, *, approved_sha256=None, observe=None):
    if approved_sha256!=fingerprint(): raise ValueError('Exact identity fingerprint required')
    from datetime import timedelta
    import secrets
    from django.db import transaction
    from django.utils import timezone
    from authentik.core.models import Application, User, Token
    from authentik.policies.models import PolicyBinding
    from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
    record={'activated':False,'delivery_confirmed':False}
    if observe is not None: observe('identity:attempted',record)
    # No network side effects inside the DB transaction. It commits only an
    # inactive identity; delivery failure must never leave an active worker.
    with transaction.atomic():
        template,count=preflight()
        user=User.objects.create(username=USER,name=NAME,type='service_account',is_active=False)
        scope=ScopeMapping.objects.create(name=SCOPE,scope_name='aster.worker',expression='return {}')
        provider=OAuth2Provider.objects.create(name=NAME,client_id=SLUG,
            client_type='confidential',client_secret=secrets.token_urlsafe(48),
            grant_types=['client_credentials'],access_token_validity='minutes=5',
            authorization_flow=template.authorization_flow,invalidation_flow=template.invalidation_flow,
            signing_key=template.signing_key,issuer_mode='per_provider',sub_mode='hashed_user_id')
        provider.property_mappings.add(scope)
        app=Application.objects.create(slug=SLUG,name=NAME,provider=provider)
        binding=PolicyBinding.objects.create(target=app,user=user,order=0,enabled=True,negate=False,timeout=30)
        token=Token.objects.create(identifier=TOKEN,user=user,intent='app_password',
            expiring=True,expires=timezone.now()+timedelta(hours=24))
        record.update(objects={name:str(obj.pk) for name,obj in (
            ('user',user),('scope',scope),('provider',provider),('application',app),
            ('binding',binding),('token',token))},existing_apps_checked=count)
    try:
        if observe is not None: observe('identity:confirmed',record)
        if deliver({'client_secret':provider.client_secret,'app_password':token.key}) is not True:
            raise ValueError('Custody delivery not confirmed')
        record['delivery_confirmed']=True
        return record
    except Exception:
        # Preserve IDs for exact cleanup. Never delete ambiguous vault writes or
        # silently create replacement identities after a partial handoff.
        raise IdentityProvisioningIncomplete(record) from None


if __name__=='__main__':
    print(json.dumps({'sha256':fingerprint(),'applied':False,'activation':False}))
