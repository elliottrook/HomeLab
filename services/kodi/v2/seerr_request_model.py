"""Pure fail-closed AsterTV contract for a future restricted Seerr broker.

This module performs no network or storage I/O.  It deliberately cannot hold a
Seerr credential or submit directly to Seerr.
"""
from dataclasses import dataclass
import re

KINDS = frozenset(('movie', 'tv'))
STATES = frozenset(('none', 'pending', 'approved', 'processing', 'available',
                    'declined', 'failed'))
ID = re.compile(r'seerr:(movie|tv):([1-9][0-9]{0,9})')


def require(ok, code):
    if not ok:
        raise ValueError(code)


@dataclass(frozen=True)
class Candidate:
    identity: str
    media_type: str
    media_id: int
    title: str
    year: str
    overview: str
    poster: str
    owned: bool
    request_id: object
    request_state: str
    seasons: tuple


@dataclass(frozen=True)
class Proposal:
    state: str
    message: str
    payload: object = None


def candidate(value):
    required = {'schema', 'identity', 'media_type', 'media_id', 'title', 'year',
                'overview', 'poster', 'owned', 'request_id', 'request_state',
                'seasons'}
    require(type(value) is dict and set(value) == required,
            'seerr-candidate-schema')
    match = ID.fullmatch(value['identity']) if isinstance(value['identity'], str) else None
    kind = value['media_type']; media_id = value['media_id']
    require(value['schema'] == 1 and kind in KINDS and type(media_id) is int
            and 0 < media_id <= 9_999_999_999 and match is not None
            and match.group(1) == kind and int(match.group(2)) == media_id,
            'seerr-candidate-identity')
    require(isinstance(value['title'], str) and 0 < len(value['title']) <= 200
            and isinstance(value['year'], str)
            and (value['year'] == '' or re.fullmatch(r'[12][0-9]{3}', value['year']))
            and isinstance(value['overview'], str) and len(value['overview']) <= 3000
            and isinstance(value['poster'], str) and len(value['poster']) <= 500,
            'seerr-candidate-text')
    require(type(value['owned']) is bool and value['request_state'] in STATES,
            'seerr-candidate-state')
    request_id = value['request_id']
    require(request_id is None or (type(request_id) is int and request_id > 0),
            'seerr-candidate-request')
    require((value['request_state'] == 'none') == (request_id is None),
            'seerr-candidate-request-state')
    require(type(value['seasons']) is list
            and all(type(item) is int and 1 <= item <= 999 for item in value['seasons'])
            and value['seasons'] == sorted(set(value['seasons'])),
            'seerr-candidate-seasons')
    require((kind == 'tv') or not value['seasons'], 'seerr-candidate-movie-seasons')
    return Candidate(value['identity'], kind, media_id, value['title'], value['year'],
                     value['overview'], value['poster'], value['owned'], request_id,
                     value['request_state'], tuple(value['seasons']))


def propose(item, selected_seasons=(), confirmed=False):
    require(isinstance(item, Candidate), 'seerr-proposal-candidate')
    if item.owned or item.request_state == 'available':
        return Proposal('unavailable', 'Already in your library')
    if item.request_state != 'none':
        return Proposal('status', 'Request already '+item.request_state)
    try:
        selected = tuple(selected_seasons)
    except TypeError as exc:
        raise ValueError('seerr-proposal-seasons') from exc
    require(all(type(value) is int for value in selected)
            and len(selected) == len(set(selected)), 'seerr-proposal-seasons')
    if item.media_type == 'movie':
        require(not selected, 'seerr-proposal-movie-seasons')
    else:
        require(bool(selected) and set(selected).issubset(item.seasons),
                'seerr-proposal-seasons')
    if confirmed is not True:
        return Proposal('confirm', 'Confirm this request')
    payload = {'schema': 1, 'action': 'request', 'authority': 'seerr',
               'candidate_id': item.identity, 'media_type': item.media_type,
               'media_id': item.media_id, 'seasons': list(sorted(selected)),
               'confirmed': True}
    return Proposal('ready', 'Ready to submit', payload)


def result(value, expected_identity):
    required = {'schema', 'candidate_id', 'request_id', 'state', 'duplicate'}
    require(isinstance(expected_identity, str)
            and type(value) is dict and set(value) == required and value['schema'] == 1
            and value['candidate_id'] == expected_identity
            and ID.fullmatch(expected_identity) is not None,
            'seerr-result-identity')
    require(type(value['request_id']) is int and value['request_id'] > 0
            and value['state'] in STATES - {'none'} and type(value['duplicate']) is bool,
            'seerr-result-state')
    return dict(value)
