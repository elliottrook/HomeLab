"""Create Bazarr's private Authentik forward-auth application inside ak shell."""
from django.db import transaction
from authentik.core.models import Application, User
from authentik.outposts.models import Outpost
from authentik.policies.models import PolicyBinding
from authentik.providers.proxy.models import ProxyProvider

with transaction.atomic():
    assert not Application.objects.filter(slug='bazarr').exists()
    assert not ProxyProvider.objects.filter(name='Provider for Bazarr').exists()
    template = ProxyProvider.objects.get(name='Provider for Nginx Proxy Manager')
    provider = ProxyProvider.objects.create(
        name='Provider for Bazarr',
        authorization_flow=template.authorization_flow,
        invalidation_flow=template.invalidation_flow,
        mode='forward_single',
        external_host='https://bazarr.elliottrook.com',
        internal_host='http://192.168.20.40:6767',
    )
    provider.set_oauth_defaults()
    provider.save()
    app = Application.objects.create(
        slug='bazarr', name='Bazarr', provider=provider,
        meta_launch_url='https://bazarr.elliottrook.com/',
    )
    PolicyBinding.objects.create(
        target=app, user=User.objects.get(username='jason'), order=0,
        enabled=True, negate=False, timeout=30,
    )
    Outpost.objects.get(name='authentik Embedded Outpost').providers.add(provider)
    print({'application': app.slug, 'provider_id': provider.pk, 'authorized_user': 'jason'})
