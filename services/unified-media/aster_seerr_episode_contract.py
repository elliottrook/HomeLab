"""Sanitized Seerr television catalogue contract for Aster episode pages."""

from __future__ import annotations

from datetime import date
import re
from typing import Any, Mapping

from aster_seerr_contract import AVAILABILITY, REQUEST_STATE, ContractError, require, text


TV_ID = re.compile(r'^seerr:tv:([1-9][0-9]{0,9})$')
IMAGE = re.compile(r'^https://image\.tmdb\.org/t/p/(?:original|w[1-9][0-9]{1,3})//?[A-Za-z0-9._/-]+$')


def _media(detail: Mapping[str, Any]) -> Mapping[str, Any]:
    value = detail.get('mediaInfo') or {}
    require(isinstance(value, Mapping), 'seerr-episode-media-invalid')
    return value


def _season_state(media: Mapping[str, Any], number: int) -> str:
    rows = media.get('seasons') or []
    require(isinstance(rows, list) and len(rows) <= 999,
            'seerr-episode-media-seasons-invalid')
    matches = [row for row in rows if isinstance(row, Mapping)
               and row.get('seasonNumber') == number]
    require(len(matches) <= 1, 'seerr-episode-media-season-duplicate')
    if not matches:
        return 'unknown'
    status = matches[0].get('status', 1)
    require(type(status) is int and status in AVAILABILITY,
            'seerr-episode-media-season-status')
    return AVAILABILITY[status]


def _request_state(media: Mapping[str, Any], number: int) -> tuple[object, str]:
    requests = media.get('requests') or []
    require(isinstance(requests, list) and len(requests) <= 100,
            'seerr-episode-requests-invalid')
    found = []
    for request in requests:
        if not isinstance(request, Mapping):
            continue
        identity, status = request.get('id'), request.get('status')
        if (type(identity) is not int or identity <= 0 or type(status) is not int
                or status not in REQUEST_STATE):
            continue
        seasons = request.get('seasons') or []
        if not isinstance(seasons, list) or len(seasons) > 999:
            raise ContractError('seerr-episode-request-seasons-invalid')
        if any(isinstance(row, Mapping) and row.get('seasonNumber') == number
               for row in seasons):
            found.append((identity, REQUEST_STATE[status]))
    return max(found, default=(None, 'none'), key=lambda row: row[0] or 0)


def _summary(media: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    number = source.get('seasonNumber')
    count = source.get('episodeCount', 0)
    require(type(number) is int and 0 <= number <= 999
            and type(count) is int and 0 <= count <= 5000,
            'seerr-episode-season-summary-invalid')
    state = _season_state(media, number)
    request_id, request_state = _request_state(media, number)
    requestable = (number > 0 and state in ('unknown', 'deleted')
                   and request_state in ('none', 'declined', 'failed'))
    return {'number': number,
            'name': text(str(source.get('name') or (
                'Specials' if number == 0 else f'Season {number}')), 200,
                         required=True),
            'episode_count': count, 'state': state,
            'request_id': request_id, 'request_state': request_state,
            'requestable': requestable}


def catalogue(media_id: int, detail: Mapping[str, Any]) -> dict[str, Any]:
    require(type(media_id) is int and 0 < media_id <= 9_999_999_999
            and isinstance(detail, Mapping) and detail.get('id') == media_id,
            'seerr-episode-catalogue-identity')
    raw = detail.get('seasons') or []
    require(isinstance(raw, list) and len(raw) <= 999,
            'seerr-episode-catalogue-seasons')
    media = _media(detail)
    seasons = [_summary(media, row) for row in raw if isinstance(row, Mapping)]
    require(len({row['number'] for row in seasons}) == len(seasons),
            'seerr-episode-catalogue-duplicate')
    seasons.sort(key=lambda row: row['number'])
    return {'schema': 1, 'candidate_id': f'seerr:tv:{media_id}',
            'title': text(str(detail.get('name') or ''), 200, required=True),
            'seasons': seasons}


def season(media_id: int, season_number: int, detail: Mapping[str, Any],
           season_detail: Mapping[str, Any]) -> dict[str, Any]:
    require(type(season_number) is int and 0 <= season_number <= 999,
            'seerr-episode-season-number')
    summary = catalogue(media_id, detail)
    selected = next((row for row in summary['seasons']
                     if row['number'] == season_number), None)
    require(selected is not None and isinstance(season_detail, Mapping)
            and season_detail.get('seasonNumber') == season_number,
            'seerr-episode-season-identity')
    raw = season_detail.get('episodes') or []
    require(isinstance(raw, list) and len(raw) <= 5000,
            'seerr-episode-season-episodes')
    episodes = []
    seen = set()
    for source in raw:
        require(isinstance(source, Mapping)
                and source.get('seasonNumber') == season_number,
                'seerr-episode-identity')
        number = source.get('episodeNumber')
        require(type(number) is int and 1 <= number <= 9999
                and number not in seen, 'seerr-episode-number')
        seen.add(number)
        aired = str(source.get('airDate') or '')
        if aired:
            try:
                date.fromisoformat(aired)
            except ValueError as error:
                raise ContractError('seerr-episode-air-date') from error
        still = str(source.get('stillPath') or '')
        require(not still or (len(still) <= 500 and IMAGE.fullmatch(still)),
                'seerr-episode-still')
        episodes.append({
            'number': number,
            'title': text(str(source.get('name') or f'Episode {number}'), 200,
                          required=True),
            'overview': text(str(source.get('overview') or ''), 1000),
            'air_date': aired,
            'still': still,
        })
    episodes.sort(key=lambda row: row['number'])
    return {'schema': 1, 'candidate_id': summary['candidate_id'],
            'title': summary['title'], 'season': selected,
            'episodes': episodes}


def season_proposal(value: Any) -> dict[str, Any]:
    required = {'schema', 'action', 'authority', 'candidate_id', 'media_id',
                'season', 'confirmed'}
    require(type(value) is dict and set(value) == required
            and value['schema'] == 1 and value['action'] == 'request-season'
            and value['authority'] == 'seerr' and value['confirmed'] is True,
            'seerr-season-proposal-invalid')
    match = TV_ID.fullmatch(value['candidate_id']) if isinstance(
        value['candidate_id'], str) else None
    require(match is not None and type(value['media_id']) is int
            and int(match.group(1)) == value['media_id']
            and type(value['season']) is int and 1 <= value['season'] <= 999,
            'seerr-season-proposal-identity')
    return dict(value)


def season_request_result(raw: Mapping[str, Any], expected: str, number: int,
                          *, duplicate: bool) -> dict[str, Any]:
    require(isinstance(raw, Mapping) and TV_ID.fullmatch(expected) is not None
            and type(number) is int and 1 <= number <= 999,
            'seerr-season-result-invalid')
    request_id, status = raw.get('id'), raw.get('status')
    require(type(request_id) is int and request_id > 0
            and type(status) is int and status in REQUEST_STATE,
            'seerr-season-result-invalid')
    return {'schema': 1, 'candidate_id': expected, 'season': number,
            'request_id': request_id, 'state': REQUEST_STATE[status],
            'duplicate': bool(duplicate)}
