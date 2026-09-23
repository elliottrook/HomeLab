"""Strict capability boundary shared by the local broker and worker."""
import hashlib
import json
import re

FIELD_NAME = 'AI summary'


def source_payload(document):
    # Only fields needed for summarization; no URLs, filenames or other fields.
    fields = ('id', 'title', 'content', 'created', 'correspondent', 'document_type', 'tags')
    return {key: document.get(key) for key in fields}


def source_hash(document):
    return hashlib.sha256(json.dumps(source_payload(document), sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def validate(request):
    if not isinstance(request, dict):
        raise ValueError('invalid_request')
    action = request.get('action')
    keys = {'page': {'action', 'page'}, 'read': {'action', 'id'},
            'publish': {'action', 'id', 'source_hash', 'summary'}}
    if action not in keys or set(request) != keys[action]:
        raise ValueError('unsupported_capability')
    value = request.get('page') if action == 'page' else request.get('id')
    if type(value) is not int or not 1 <= value <= (1000 if action == 'page' else 2**31-1):
        raise ValueError('invalid_id')
    if action == 'publish':
        if not isinstance(request['source_hash'], str) or not re.fullmatch('[0-9a-f]{64}', request['source_hash']):
            raise ValueError('invalid_hash')
        if not isinstance(request['summary'], str) or not request['summary'].strip() or len(request['summary']) > 3000:
            raise ValueError('invalid_summary')
    return action
