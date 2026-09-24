"""Source-local capabilities. Imported only after Django setup.

Worker cannot supply paths, credentials, field IDs, ORM filters, or commands.
The trusted bridge has database authority, but exposes only the fixed summary
field mutation. A dedicated writer identity gates activation; no writer token
is issued. This code is a privileged boundary and requires deployment review.
"""
import json
import urllib.error
import urllib.request

from broker_contract import FIELD_NAME, source_hash, source_payload, validate


def api_read(path, reader):
    from rest_framework.authtoken.models import Token
    token = Token.objects.get(user=reader)
    request = urllib.request.Request('http://127.0.0.1:8000' + path,
                                     headers={'Authorization': 'Token ' + token.key}, method='GET')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise ValueError('redirect_denied')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=20) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError('response_limit')
    return json.loads(raw)


def dispatch(request, read_api=api_read):
    from django.contrib.auth.models import User
    from django.db import transaction
    from documents.models import CustomField, CustomFieldInstance, Document
    from documents.permissions import permitted_document_ids
    action = validate(request)
    reader = User.objects.get(username='ai-paperless-reader')
    if not reader.is_active or reader.is_superuser or reader.is_staff or reader.get_all_permissions() != {'documents.view_document'}:
        raise ValueError('reader_permission_drift')
    if action == 'page':
        response = read_api(f'/api/documents/?page={request["page"]}&page_size=25&ordering=id', reader)
        return {'documents': [source_payload(row) for row in response['results']],
                'more': bool(response['next']), 'count': response['count']}
    path = f'/api/documents/{request["id"]}/'
    document = read_api(path, reader)  # native API enforces object visibility
    if action == 'read':
        return source_payload(document)
    writer = User.objects.get(username='ai-paperless-summary-writer')
    required = {'documents.add_customfieldinstance', 'documents.change_customfieldinstance'}
    if not writer.is_active or writer.is_staff or writer.is_superuser or writer.get_all_permissions() != required:
        raise ValueError('writer_permission_drift')
    if source_hash(document) != request['source_hash']:
        raise ValueError('stale_source')
    with transaction.atomic():
        # Native API is authoritative for source content. Recheck the underlying
        # document version and current permission inside the write transaction.
        doc = Document.objects.select_for_update().get(pk=request['id'])
        if not Document.objects.filter(pk=doc.pk, id__in=permitted_document_ids(reader)).exists():
            raise ValueError('access_revoked')
        current = read_api(path, reader)
        if source_hash(current) != request['source_hash']:
            raise ValueError('stale_source')
        field = CustomField.objects.get(name=FIELD_NAME, data_type='longtext')
        # Only the single field's storage column is addressed. Never PATCH a
        # document or replace its whole custom_fields collection.
        rows = CustomFieldInstance.objects.filter(document=doc, field=field)
        if rows.exists():
            rows.update(value_long_text=request['summary'])
        else:
            CustomFieldInstance.objects.bulk_create([
                CustomFieldInstance(document=doc, field=field,
                                    value_long_text=request['summary'])])
        # Deliberately bypass post_save hooks: Paperless may otherwise rename
        # files when a filename template references custom fields.
        from documents.caching import clear_document_caches
        transaction.on_commit(lambda: clear_document_caches(doc.pk))
    return {'published': True}
