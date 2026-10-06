"""Idempotently provision the private Authentik forward-auth application."""

from django.db import transaction

from authentik.core.models import Application
from authentik.outposts.models import Outpost
from authentik.policies.models import PolicyBinding
from authentik.providers.proxy.models import ProxyProvider


EXTERNAL_HOST = "https://recommendations.elliottrook.com"

with transaction.atomic():
    template_app = Application.objects.get(slug="nginx-proxy-manager")
    template_provider = ProxyProvider.objects.get(name="Provider for Nginx Proxy Manager")
    owner_binding = PolicyBinding.objects.get(target=template_app.pk, user_id__isnull=False)
    provider, _ = ProxyProvider.objects.update_or_create(
        name="Provider for Unified Media Recommendations",
        defaults={
            "authorization_flow": template_provider.authorization_flow,
            "invalidation_flow": template_provider.invalidation_flow,
            "mode": "forward_single",
            "external_host": EXTERNAL_HOST,
            "internal_host": "http://192.168.20.40:8787",
        },
    )
    provider.set_oauth_defaults()
    provider.save()
    application, _ = Application.objects.update_or_create(
        slug="unified-media-recommendations",
        defaults={
            "name": "Unified Media Recommendations",
            "provider": provider,
            "meta_launch_url": EXTERNAL_HOST + "/",
        },
    )
    PolicyBinding.objects.update_or_create(
        target=application,
        user_id=owner_binding.user_id,
        defaults={"order": 0, "enabled": True, "negate": False, "timeout": 30},
    )
    outpost = Outpost.objects.get(name="authentik Embedded Outpost")
    outpost.providers.add(provider)

print({
    "application": application.slug,
    "provider": provider.name,
    "mode": provider.mode,
    "external_host": provider.external_host,
    "owner_bindings": PolicyBinding.objects.filter(
        target=application.pk, user_id__isnull=False, enabled=True
    ).count(),
    "outpost_attached": outpost.providers.filter(pk=provider.pk).exists(),
})
