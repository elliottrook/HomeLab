"""Read-only installed Authentik check; run through ak shell, not local unittest.
Uses synthetic request/session objects and never issues real tokens.
"""
from types import SimpleNamespace as NS
from datetime import timedelta
from unittest.mock import patch
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from authentik.core.models import User
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.views import authorize as a
from authentik.flows.models import Flow
from authentik.flows.planner import FlowPlanner, FlowNonApplicableException
p=OAuth2Provider.objects.get(pk=26)
assert p.authentication_flow.slug=='aster-companion-reauthentication'
f=Flow.objects.get(slug='aster-companion-passwordless')
u=User.objects.get(username='jason');r=RequestFactory().get('/application/o/authorize/');r.user=u;r.session={}
v=a.AuthorizationFlowInitView();v.request=r;v.provider=p;v.params=NS(max_age=0,prompt=['login'],scope=['openid'],provider=p)
e=NS(pk='synthetic-login-before',created=timezone.now()-timedelta(minutes=10))
v.handle_no_permission=lambda:'fresh-flow-required'
with patch.object(a,'get_login_event',return_value=e):
 assert v.get(r)=='fresh-flow-required'
 assert v.get(r)=='fresh-flow-required'
class Reauthenticated(Exception):pass
e.pk='synthetic-login-after'
with patch.object(a,'get_login_event',return_value=e),patch.object(a.UserInfoView,'get_scope_descriptions',return_value=[]),patch.object(a,'FlowPlanner',side_effect=Reauthenticated):
 try:v.get(r)
 except Reauthenticated:pass
 else:raise AssertionError('New login event did not advance')
try:FlowPlanner(f)._check_authentication(r,{})
except FlowNonApplicableException:pass
else:raise AssertionError('Expected original flow to reject existing login')
f.authentication='none'
FlowPlanner(f)._check_authentication(r,{})
r.user=AnonymousUser();FlowPlanner(f)._check_authentication(r,{})
print('PASS: prompt=login forces existing/same-session reauthentication; new login event advances; candidate flow admits authenticated and anonymous users to required stages. No sessions or tokens created.')
