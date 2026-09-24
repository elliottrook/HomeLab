"""Read-only permission checks; run via deployed Paperless manage.py shell.

Evaluates permission gates directly. Does not dispatch mutation handlers,
create fixtures, issue tokens, or read document contents. This is not a full
HTTP/token or object-level authorization test.
"""
import json
from types import SimpleNamespace

from django.contrib.auth.models import User
from documents.permissions import PaperlessObjectPermissions, PaperlessNotePermissions
from documents.views import DocumentViewSet
from rest_framework.authtoken.models import Token

user = User.objects.get(username="ai-paperless-reader")
assert user.is_active and not user.is_staff and not user.is_superuser
assert not user.has_usable_password() and not user.groups.exists()
assert user.get_all_permissions() == {"documents.view_document"}
assert not Token.objects.filter(user=user).exists()
view = DocumentViewSet()
view.queryset = view.queryset.none()
checks = {}
for method, expected in {
    "GET": True, "HEAD": True, "OPTIONS": True,
    "POST": False, "PUT": False, "PATCH": False, "DELETE": False,
}.items():
    request = SimpleNamespace(user=user, method=method)
    allowed = PaperlessObjectPermissions().has_permission(request, view)
    assert allowed == expected, (method, allowed)
    checks[method] = allowed
for method in ("POST", "DELETE"):
    request = SimpleNamespace(user=user, method=method)
    assert not PaperlessNotePermissions().has_permission(request, view)
print(json.dumps({"document_model_gate": checks, "note_mutation_gates": "denied",
                  "scope": "permission classes only; no mutation handlers invoked"}))
