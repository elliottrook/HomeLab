"""Apply only with explicit approval, via manage.py shell in Paperless.

Creates missing integration objects atomically. Existing unexpected objects
abort rather than being overwritten. No existing document permissions changed.
"""
import json
from django.contrib.auth.models import Permission, User
from django.db import transaction
from documents.models import CustomField, Workflow, WorkflowAction, WorkflowTrigger
from rest_framework.authtoken.models import Token

with transaction.atomic():
    reader = User.objects.get(username='ai-paperless-reader')
    assert reader.is_active and not reader.is_staff and not reader.is_superuser
    assert reader.get_all_permissions() == {'documents.view_document'}
    writer_name = 'ai-paperless-summary-writer'
    assert not User.objects.filter(username=writer_name).exists(), 'Writer exists; inspect before applying'
    assert not CustomField.objects.filter(name='AI summary').exists(), 'Field exists; inspect before applying'
    assert not Workflow.objects.filter(name='AI summary reader access').exists(), 'Workflow exists; inspect before applying'
    assert not Token.objects.filter(user=reader).exists(), 'Reader token exists; inspect custody before applying'
    writer = User(username=writer_name, is_active=True, is_staff=False, is_superuser=False)
    writer.set_unusable_password()
    writer.save()
    permissions = Permission.objects.filter(content_type__app_label='documents', codename__in=['add_customfieldinstance', 'change_customfieldinstance'])
    assert permissions.count() == 2
    writer.user_permissions.add(*permissions)
    field = CustomField.objects.create(name='AI summary', data_type='longtext')
    Token.objects.create(user=reader)  # Remains in Paperless DB; never returned.
    workflow = Workflow.objects.create(name='AI summary reader access', enabled=True, order=1000)
    trigger = WorkflowTrigger.objects.create(type=WorkflowTrigger.WorkflowTriggerType.DOCUMENT_ADDED)
    action = WorkflowAction.objects.create(type=WorkflowAction.WorkflowActionType.ASSIGNMENT)
    action.assign_view_users.add(reader)
    workflow.triggers.add(trigger)
    workflow.actions.add(action)
    print(json.dumps({'writer': writer_name, 'field_id': field.pk, 'workflow_id': workflow.pk,
                      'reader_token_created_in_place': True, 'writer_token_created': False,
                      'existing_document_grants_changed': False}))
