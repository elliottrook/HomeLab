"""Offline exact-turn answer recovery candidate; no Codex read or gateway route.

The caller must obtain completed_sha256 from an authenticated owner-scoped
Gateway record and the snapshot from the pinned Codex account. Never accept
those values from a user request body or use this module to start a new turn.
"""
import hashlib
import re

if __package__:
    from .recovery import reconcile
else:
    from recovery import reconcile


class RecoveryUnavailable(Exception):
    """No answer is released; intentionally carries no provider content."""


def recover_completed(store, authenticated_owner, job_id, completed_sha256, snapshot):
    if not authenticated_owner or not isinstance(job_id, str):
        raise RecoveryUnavailable('Answer unavailable')
    if not isinstance(completed_sha256, str) or not re.fullmatch('[a-f0-9]{64}', completed_sha256):
        raise RecoveryUnavailable('Answer unavailable')
    row = store.inspect_owned(job_id, authenticated_owner)
    if not row or row[0] != 'completed' or not row[1] or not row[2]:
        raise RecoveryUnavailable('Answer unavailable')
    if not isinstance(snapshot, dict):
        raise RecoveryUnavailable('Answer unavailable')
    thread = snapshot.get('thread')
    if not isinstance(thread, dict) or thread.get('id') != row[1]:
        raise RecoveryUnavailable('Answer unavailable')
    turns = thread.get('turns')
    if not isinstance(turns, list):
        raise RecoveryUnavailable('Answer unavailable')
    matches = [turn for turn in turns if isinstance(turn, dict) and turn.get('id') == row[2]]
    if len(matches) != 1 or matches[0].get('itemsView') != 'full':
        raise RecoveryUnavailable('Answer unavailable')
    items = matches[0].get('items')
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise RecoveryUnavailable('Answer unavailable')
    final_ids = [item.get('id') for item in items
                 if item.get('type') == 'agentMessage' and item.get('phase') == 'final_answer']
    if not final_ids or len(final_ids) != len(set(final_ids)):
        raise RecoveryUnavailable('Answer unavailable')
    try:
        result = reconcile(store, job_id, snapshot)
        answer = result['answer']
        if (result['state'] != 'completed' or not isinstance(answer, str) or
                not answer.strip() or hashlib.sha256(answer.encode()).hexdigest() != completed_sha256):
            raise RecoveryUnavailable('Answer unavailable')
        return answer
    except Exception:
        raise RecoveryUnavailable('Answer unavailable') from None
