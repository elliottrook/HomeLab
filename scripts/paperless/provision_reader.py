"""Run with Django initialized by manage.py shell. Dry-run unless explicitly applied.

Example inside the Paperless container, after operational approval:
PAPERLESS_READER_APPLY=1 python3 manage.py shell < provision_reader.py
No tokens are issued and no document permissions are changed.
"""
import json
import os

from django.contrib.auth.models import Permission, User
from django.db import transaction

USERNAME = "ai-paperless-reader"
EXPECTED = {"documents.view_document"}
apply = os.environ.get("PAPERLESS_READER_APPLY") == "1"

with transaction.atomic():
    permission = Permission.objects.get(
        content_type__app_label="documents", codename="view_document"
    )
    user = User.objects.filter(username=USERNAME).first()
    if user is not None:
        if (
            user.is_staff
            or user.is_superuser
            or not user.is_active
            or user.has_usable_password()
            or user.groups.exists()
            or user.get_all_permissions() != EXPECTED
        ):
            raise RuntimeError("Existing reader differs from expected state; no changes made")
        outcome = "already_matches"
    elif not apply:
        outcome = "would_create"
    else:
        user = User(username=USERNAME, is_active=True, is_staff=False, is_superuser=False)
        user.set_unusable_password()
        user.save()
        user.user_permissions.add(permission)
        # Re-read to avoid permission-cache ambiguity.
        user = User.objects.get(pk=user.pk)
        if user.get_all_permissions() != EXPECTED or user.has_usable_password():
            raise RuntimeError("Reader verification failed; transaction rolled back")
        outcome = "created"

print(json.dumps({
    "username": USERNAME,
    "outcome": outcome,
    "model_permissions": sorted(EXPECTED),
    "tokens_issued": False,
    "document_access_changed": False,
}))
