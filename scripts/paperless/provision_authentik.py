"""Create only Paperless's private forward-auth integration inside ak shell."""
from django.db import transaction
from authentik.core.models import Application, User
from authentik.outposts.models import Outpost
from authentik.policies.models import PolicyBinding
from authentik.providers.proxy.models import ProxyProvider
with transaction.atomic():
    assert not Application.objects.filter(slug='paperless').exists()
    assert not ProxyProvider.objects.filter(name='Provider for Paperless').exists()
    template=ProxyProvider.objects.get(name='Provider for Nginx Proxy Manager')
    provider=ProxyProvider.objects.create(name='Provider for Paperless',authorization_flow=template.authorization_flow,invalidation_flow=template.invalidation_flow,mode='forward_single',external_host='https://paperless.elliottrook.com',internal_host='http://192.168.70.15:8000')
    provider.set_oauth_defaults()
    provider.save()
    app=Application.objects.create(slug='paperless',name='Paperless',provider=provider,meta_launch_url='https://paperless.elliottrook.com/')
    PolicyBinding.objects.create(target=app,user=User.objects.get(username='jason'),order=0,enabled=True,negate=False,timeout=30)
    Outpost.objects.get(name='authentik Embedded Outpost').providers.add(provider)
    print({'application':app.slug,'provider_id':provider.pk,'authorized_user':'jason'})
