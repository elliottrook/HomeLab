"""Pure Seerr episode-catalogue parser and local-library merge.

Local Kodi episodes always win. Catalogue-only rows never acquire a playable
Kodi identity, so the player boundary cannot mistake a request shortcut for
owned media.
"""
from dataclasses import dataclass, replace
from datetime import date
import re

from series_model import Episode, Season

IDENTITY = re.compile(r'seerr:tv:([1-9][0-9]{0,9})')
STATES = frozenset(('unknown', 'pending', 'processing', 'partial', 'available',
                    'blocklisted', 'deleted'))
REQUESTS = frozenset(('none', 'pending', 'approved', 'processing', 'available',
                      'declined', 'failed'))
IMAGE = re.compile(r'https://image\.tmdb\.org/t/p/(?:original|w[1-9][0-9]{1,3})//?[A-Za-z0-9._/-]+')


def require(value, code):
    if not value:
        raise ValueError(code)


@dataclass(frozen=True)
class CatalogueSeason:
    number: int
    name: str
    episode_count: int
    state: str
    request_id: object
    request_state: str
    requestable: bool


@dataclass(frozen=True)
class Catalogue:
    candidate_id: str
    media_id: int
    title: str
    seasons: tuple


@dataclass(frozen=True)
class CatalogueEpisode:
    number: int
    title: str
    overview: str
    air_date: str
    still: str


@dataclass(frozen=True)
class CatalogueSeasonDetail:
    candidate_id: str
    title: str
    season: CatalogueSeason
    episodes: tuple


def season_proposal(catalogue, number, confirmed=False):
    require(isinstance(catalogue, Catalogue) and type(number) is int
            and 1 <= number <= 999,
            'series-catalogue-proposal-identity')
    summary = next((row for row in catalogue.seasons if row.number == number), None)
    require(summary is not None and summary.requestable,
            'series-catalogue-proposal-unavailable')
    if confirmed is not True:
        return None
    return {'schema': 1, 'action': 'request-season', 'authority': 'seerr',
            'candidate_id': catalogue.candidate_id,
            'media_id': catalogue.media_id, 'season': number,
            'confirmed': True}


def season_result(value, catalogue, number):
    keys = {'schema', 'candidate_id', 'season', 'request_id', 'state', 'duplicate'}
    require(isinstance(catalogue, Catalogue) and type(value) is dict
            and set(value) == keys and value['schema'] == 1
            and value['candidate_id'] == catalogue.candidate_id
            and value['season'] == number
            and type(value['request_id']) is int and value['request_id'] > 0
            and value['state'] in REQUESTS - {'none'}
            and type(value['duplicate']) is bool,
            'series-catalogue-request-result')
    return dict(value)


def _summary(value):
    keys = {'number', 'name', 'episode_count', 'state', 'request_id',
            'request_state', 'requestable'}
    require(type(value) is dict and set(value) == keys,
            'series-catalogue-season-schema')
    number, count = value['number'], value['episode_count']
    request_id = value['request_id']
    require(type(number) is int and 0 <= number <= 999
            and isinstance(value['name'], str) and 0 < len(value['name']) <= 200
            and type(count) is int and 0 <= count <= 5000
            and value['state'] in STATES
            and (request_id is None or (type(request_id) is int and request_id > 0))
            and value['request_state'] in REQUESTS
            and type(value['requestable']) is bool,
            'series-catalogue-season-value')
    return CatalogueSeason(number, value['name'], count, value['state'],
                           request_id, value['request_state'], value['requestable'])


def parse_catalogue(value):
    require(type(value) is dict
            and set(value) == {'schema', 'candidate_id', 'title', 'seasons'}
            and value['schema'] == 1 and isinstance(value['title'], str)
            and 0 < len(value['title']) <= 200 and type(value['seasons']) is list
            and len(value['seasons']) <= 999,
            'series-catalogue-schema')
    match = IDENTITY.fullmatch(value['candidate_id']) if isinstance(
        value['candidate_id'], str) else None
    require(match is not None, 'series-catalogue-identity')
    seasons = tuple(_summary(row) for row in value['seasons'])
    require(tuple(row.number for row in seasons) == tuple(sorted(
        {row.number for row in seasons})), 'series-catalogue-season-order')
    return Catalogue(value['candidate_id'], int(match.group(1)), value['title'], seasons)


def parse_season(value, catalogue, number):
    require(isinstance(catalogue, Catalogue) and type(number) is int
            and type(value) is dict
            and set(value) == {'schema', 'candidate_id', 'title', 'season', 'episodes'}
            and value['schema'] == 1 and value['candidate_id'] == catalogue.candidate_id
            and value['title'] == catalogue.title and type(value['episodes']) is list
            and len(value['episodes']) <= 5000,
            'series-catalogue-detail-schema')
    summary = _summary(value['season'])
    expected = next((row for row in catalogue.seasons if row.number == number), None)
    require(summary == expected, 'series-catalogue-detail-season')
    rows = []
    for source in value['episodes']:
        require(type(source) is dict
                and set(source) == {'number', 'title', 'overview', 'air_date', 'still'},
                'series-catalogue-episode-schema')
        episode = source['number']; still = source['still']
        aired = source['air_date']
        require(type(episode) is int and 1 <= episode <= 9999
                and isinstance(source['title'], str) and 0 < len(source['title']) <= 200
                and isinstance(source['overview'], str) and len(source['overview']) <= 1000
                and isinstance(aired, str) and len(aired) <= 10
                and isinstance(still, str) and (not still or IMAGE.fullmatch(still)),
                'series-catalogue-episode-value')
        if aired:
            try: date.fromisoformat(aired)
            except ValueError as error: raise ValueError('series-catalogue-episode-date') from error
        rows.append(CatalogueEpisode(episode, source['title'], source['overview'],
                                     aired, still))
    require(tuple(row.number for row in rows) == tuple(sorted(
        {row.number for row in rows})), 'series-catalogue-episode-order')
    return CatalogueSeasonDetail(catalogue.candidate_id, catalogue.title,
                                 summary, tuple(rows))


def merge_page(page, catalogue, loaded=()):
    require(isinstance(catalogue, Catalogue), 'series-catalogue-merge-catalogue')
    details = {row.season.number: row for row in loaded}
    require(len(details) == len(tuple(loaded))
            and all(isinstance(row, CatalogueSeasonDetail)
                    and row.candidate_id == catalogue.candidate_id
                    for row in details.values()), 'series-catalogue-merge-detail')
    local = {group.number: group for group in page.seasons}
    summaries = {row.number: row for row in catalogue.seasons}
    regular = sorted({number for number in (*local, *summaries)
                      if type(number) is int and number > 0})
    numbers = regular
    if 0 in local or 0 in summaries:
        numbers.append(0)
    if None in local:
        numbers.append(None)
    groups = []
    for number in numbers:
        local_rows = list(local.get(number, Season(number, '', ())).episodes)
        detail = details.get(number)
        summary = summaries.get(number)
        if detail is not None:
            by_number = {row.number: row for row in local_rows
                         if row.number is not None}
            merged = []
            for remote in detail.episodes:
                owned = by_number.pop(remote.number, None)
                if owned is not None:
                    merged.append(owned)
                else:
                    merged.append(Episode(
                        None, number, remote.number, remote.title, remote.overview,
                        remote.still, None, remote.air_date, False, False, None,
                        None, '', True, bool(summary and summary.requestable),
                        summary.request_state if summary else 'none'))
            merged.extend(row for row in local_rows
                          if row.number is None or row.number in by_number)
            local_rows = sorted(merged, key=lambda row: (
                row.number is None, row.number or 0,
                row.episode_id is None, row.episode_id or 0))
        label = ('Other episodes' if number is None else 'Specials' if number == 0
                 else (summary.name if summary else f'Season {number}'))
        groups.append(Season(number, label, tuple(local_rows)))
    return replace(page, seasons=tuple(groups))
