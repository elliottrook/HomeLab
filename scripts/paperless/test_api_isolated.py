"""Test installed Paperless API in a disposable DB with all socket connects denied.

Run as plain Python in the webserver container, NOT manage.py shell. All runtime
settings must be redirected before django.setup(). No production tokens or data.
"""
import json
import os
import socket
import tempfile
from pathlib import Path
from unittest.mock import patch


def blocked(*args, **kwargs):
    raise RuntimeError('Network disabled in isolated API test')


with tempfile.TemporaryDirectory(prefix='paperless-api-test-') as temporary:
    root = Path(temporary)
    for env, suffix in [('PAPERLESS_DATA_DIR', 'data'), ('PAPERLESS_MEDIA_ROOT', 'media'),
                        ('PAPERLESS_CONSUMPTION_DIR', 'consume'), ('PAPERLESS_LOGGING_DIR', 'logs'),
                        ('PAPERLESS_SCRATCH_DIR', 'scratch')]:
        target = root / suffix
        target.mkdir(mode=0o700)
        os.environ[env] = str(target)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'paperless.settings'
    os.environ['PAPERLESS_AI_ENABLED'] = 'false'
    os.environ['PAPERLESS_SECRET_KEY'] = 'synthetic-test-key-not-a-production-secret'
    from django.conf import settings
    assert str(settings.DATA_DIR).startswith(temporary + '/')
    settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(root / 'test.sqlite3')}}
    settings.CACHES = {alias: {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'synthetic-' + alias} for alias in settings.CACHES}
    settings.CACHALOT_ENABLED = False
    settings.CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
    settings.CELERY_BROKER_URL = 'memory://'
    settings.CELERY_RESULT_BACKEND = 'cache+memory://'
    settings.CELERY_TASK_ALWAYS_EAGER = False
    settings.LOGGING = {'version': 1, 'disable_existing_loggers': True}
    settings.ALLOWED_HOSTS = ['testserver']
    settings.SECURE_SSL_REDIRECT = False
    with patch.object(socket.socket, 'connect', blocked), patch.object(socket, 'create_connection', blocked):
        import django
        django.setup()
        from django.core.management import call_command
        from django.db import connection
        assert str(connection.settings_dict['NAME']).startswith(temporary + '/')
        call_command('migrate', verbosity=0, interactive=False)
        from django.contrib.auth.models import User, Permission
        from documents.models import Document
        from guardian.shortcuts import assign_perm, remove_perm
        from rest_framework.authtoken.models import Token
        from rest_framework.test import APIClient
        reader = User.objects.create_user('synthetic-reader', password=None)
        owner = User.objects.create_user('synthetic-owner', password=None)
        reader.user_permissions.add(Permission.objects.get(content_type__app_label='documents', codename='view_document'))
        Document.objects.bulk_create([
            Document(title='SYNTHETIC allowed', content='SYNTHETIC warranty ends December.', mime_type='text/plain', checksum='a'*64, owner=owner),
            Document(title='SYNTHETIC hidden', content='SYNTHETIC private fixture.', mime_type='text/plain', checksum='b'*64, owner=owner),
        ])
        allowed, hidden = list(Document.objects.order_by('id'))
        token = Token.objects.create(user=reader)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        checks = {}
        response = client.get('/api/documents/')
        assert response.status_code == 200 and response.json()['count'] == 0
        checks['ungranted_owned_documents_hidden'] = True
        assign_perm('view_document', reader, allowed)
        response = client.get(f'/api/documents/{allowed.pk}/')
        assert response.status_code == 200 and response.json()['content'] == allowed.content
        checks['token_read_granted_document'] = response.status_code
        response = client.get(f'/api/documents/{hidden.pk}/')
        assert response.status_code in (403, 404)
        checks['other_document_denied'] = response.status_code
        for method in ('patch', 'put', 'delete'):
            response = getattr(client, method)(f'/api/documents/{allowed.pk}/', {'title': 'FORBIDDEN'}, format='json')
            assert response.status_code == 403, (method, response.status_code)
            checks[method + '_denied'] = response.status_code
        response = client.post(f'/api/documents/{allowed.pk}/notes/', {'note': 'FORBIDDEN'}, format='json')
        assert response.status_code == 403, response.status_code
        checks['note_write_denied'] = response.status_code
        allowed.refresh_from_db()
        assert allowed.title == 'SYNTHETIC allowed' and Document.objects.count() == 2
        remove_perm('view_document', reader, allowed)
        response = client.get(f'/api/documents/{allowed.pk}/')
        assert response.status_code in (403, 404)
        checks['revocation_denied'] = response.status_code
        client.credentials(HTTP_AUTHORIZATION='Token synthetic-invalid-token')
        response = client.get('/api/documents/')
        assert response.status_code in (401, 403)
        checks['invalid_token_denied'] = response.status_code
        # Optional broker module supplied from the local repository in memory.
        import sys
        if 'django_bridge' in sys.modules:
            from django_bridge import dispatch
            from broker_contract import FIELD_NAME, source_hash
            from documents.models import CustomField, CustomFieldInstance
            from django.db.models.signals import post_save
            reader.username = 'ai-paperless-reader'
            reader.save(update_fields=['username'])
            writer = User.objects.create_user('ai-paperless-summary-writer', password=None)
            writer.user_permissions.add(*Permission.objects.filter(
                content_type__app_label='documents',
                codename__in=['add_customfieldinstance', 'change_customfieldinstance']))
            assign_perm('view_document', reader, allowed)
            client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
            def read_api(path, user):
                response = client.get(path)
                if response.status_code != 200:
                    raise ValueError('api_denied')
                return response.json()
            field = CustomField.objects.create(name=FIELD_NAME, data_type='longtext')
            other = CustomField.objects.create(name='SYNTHETIC other', data_type='longtext')
            CustomFieldInstance.objects.bulk_create([
                CustomFieldInstance(document=allowed, field=other, value_long_text='untouched')])
            original = Document.objects.filter(pk=allowed.pk).values().get()
            document = dispatch({'action': 'read', 'id': allowed.pk}, read_api)
            request = {'action': 'publish', 'id': allowed.pk,
                       'source_hash': source_hash(document), 'summary': 'Synthetic warranty summary.'}
            def no_save_signal(*args, **kwargs):
                raise AssertionError('Write broker must not invoke file-moving save signals')
            post_save.connect(no_save_signal, sender=CustomFieldInstance, weak=False)
            try:
                assert dispatch(request, read_api) == {'published': True}
                assert dispatch(request, read_api) == {'published': True}
            finally:
                post_save.disconnect(no_save_signal, sender=CustomFieldInstance)
            assert CustomFieldInstance.objects.get(document=allowed, field=field).value_long_text == request['summary']
            assert CustomFieldInstance.objects.get(document=allowed, field=other).value_long_text == 'untouched'
            assert Document.objects.filter(pk=allowed.pk).values().get() == original
            for bad in [dict(request, title='FORBIDDEN'), dict(request, action='delete'), dict(request, source_hash='0'*64), dict(request, id=hidden.pk)]:
                try:
                    dispatch(bad, read_api)
                except ValueError:
                    pass
                else:
                    raise AssertionError('Forbidden broker request succeeded')
            remove_perm('view_document', reader, allowed)
            try:
                dispatch(request, read_api)
            except ValueError:
                pass
            else:
                raise AssertionError('Revoked broker request succeeded')
            checks['broker_field_only_and_idempotent'] = True
            checks['broker_stale_hidden_revoked_and_extra_fields_denied'] = True
            checks['broker_does_not_trigger_file_moves'] = True
        print(json.dumps({'isolated_database': True, 'network_disabled': True, 'checks': checks}))
        connection.close()
