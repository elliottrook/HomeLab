"""Run inside `ak shell` to provision owner-only Content Desk forward auth."""

from django.db import transaction
from authentik.core.models import Application
from authentik.outposts.models import Outpost
from authentik.policies.models import PolicyBinding
from authentik.providers.proxy.models import ProxyProvider

with transaction.atomic():
    template_app = Application.objects.get(slug="aster-knowledge-wiki")
    template_provider = ProxyProvider.objects.get(name="Provider for Aster Knowledge Wiki")
    owner_binding = PolicyBinding.objects.get(target=template_app.pk, user_id__isnull=False)
    provider, _ = ProxyProvider.objects.update_or_create(
        name="Provider for Photography Content Desk",
        defaults={"authorization_flow": template_provider.authorization_flow,
                  "invalidation_flow": template_provider.invalidation_flow,
                  "mode": "forward_single",
                  "external_host": "https://tcf.elliottrook.com",
                  "internal_host": "http://192.168.20.35:8080"},
    )
    application, _ = Application.objects.update_or_create(
        slug="photography-content-desk",
        defaults={"name": "Photography Content Desk", "provider": provider,
                  "meta_launch_url": "https://tcf.elliottrook.com/"},
    )
    PolicyBinding.objects.update_or_create(
        target=application, user_id=owner_binding.user_id,
        defaults={"order": 0, "enabled": True, "negate": False, "timeout": 30},
    )
    outpost = Outpost.objects.get(name="authentik Embedded Outpost")
    outpost.providers.add(provider)

print({"application": application.slug, "provider": provider.name,
       "owner_bindings": PolicyBinding.objects.filter(
           target=application.pk, user_id__isnull=False, enabled=True).count(),
       "outpost_attached": outpost.providers.filter(pk=provider.pk).exists()})
