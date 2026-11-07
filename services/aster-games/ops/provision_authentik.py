"""Idempotently provision the two Aster Games forward-auth applications."""

from django.db import transaction

from authentik.core.models import Application
from authentik.outposts.models import Outpost
from authentik.flows.models import Flow
from authentik.policies.models import PolicyBinding
from authentik.providers.proxy.models import ProxyProvider


TARGETS = (
    (
        "Provider for Aster Games",
        "aster-games",
        "Aster Games",
        "https://games.elliottrook.com",
        "http://192.168.20.38:8080",
    ),
    (
        "Provider for Aster Games ROMarr",
        "aster-games-romarr",
        "Aster Games ROMarr",
        "https://romarr.elliottrook.com",
        "http://192.168.20.38:6868",
    ),
)


with transaction.atomic():
    template_app = Application.objects.get(slug="nginx-proxy-manager")
    template_provider = ProxyProvider.objects.get(name="Provider for Nginx Proxy Manager")
    owner_binding = PolicyBinding.objects.get(target=template_app.pk, user_id__isnull=False)
    passkey_flow = Flow.objects.get(slug="aster-companion-passwordless")
    outpost = Outpost.objects.get(name="authentik Embedded Outpost")
    results = []
    for provider_name, slug, name, external_host, internal_host in TARGETS:
        provider, _ = ProxyProvider.objects.update_or_create(
            name=provider_name,
            defaults={
                "authorization_flow": template_provider.authorization_flow,
                "invalidation_flow": template_provider.invalidation_flow,
                "authentication_flow": passkey_flow,
                "mode": "forward_single",
                "external_host": external_host,
                "internal_host": internal_host,
            },
        )
        provider.set_oauth_defaults()
        provider.save()
        application, _ = Application.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "provider": provider,
                "meta_launch_url": external_host + "/",
            },
        )
        PolicyBinding.objects.update_or_create(
            target=application,
            user_id=owner_binding.user_id,
            defaults={"order": 0, "enabled": True, "negate": False, "timeout": 30},
        )
        outpost.providers.add(provider)
        results.append(
            {
                "application": application.slug,
                "provider": provider.name,
                "external_host": provider.external_host,
                "owner_bindings": PolicyBinding.objects.filter(
                    target=application.pk, user_id__isnull=False, enabled=True
                ).count(),
                "outpost_attached": outpost.providers.filter(pk=provider.pk).exists(),
            }
        )

print({"applications": results})
