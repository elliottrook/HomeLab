"""Truthful recommendation projection for the owned Books catalogue.

Only source-owned metadata and confirmed shared-household listening records may
influence a recommendation.  Private progress details and transient metadata
are removed before records reach the presentation feed.
"""
from collections import Counter
import math


MAX_ITEMS = 2000


def require(value, code):
    if not value:
        raise ValueError(code)


def _tokens(value, maximum, code):
    require(isinstance(value, list) and len(value) <= maximum, code)
    result = []
    for item in value:
        if isinstance(item, dict):
            item = item.get('name')
        require(isinstance(item, str) and 0 < len(item.strip()) <= 120, code)
        token = item.strip()
        if token.casefold() not in {entry.casefold() for entry in result}:
            result.append(token)
    return tuple(result)


def _progress(value):
    if value is None:
        return None
    require(isinstance(value, dict), 'books-landing-progress')
    duration, position = value.get('duration'), value.get('currentTime')
    finished = value.get('isFinished')
    hidden = value.get('hideFromContinueListening', False)
    require(type(duration) in (int, float) and type(duration) is not bool
            and math.isfinite(duration) and 0 <= duration <= 604800
            and type(position) in (int, float) and type(position) is not bool
            and math.isfinite(position) and 0 <= position
            and type(finished) is bool and type(hidden) is bool,
            'books-landing-progress')
    require((finished and duration == 0) or position <= duration,
            'books-landing-progress')
    return duration, position, finished, hidden


def recommend_audio(rows):
    """Attach bounded recommendation score/reason, then discard raw signals."""
    require(isinstance(rows, list) and len(rows) <= MAX_ITEMS,
            'books-landing-input')
    prepared = []
    affinity = {'audiobook': {'authors': Counter(), 'genres': Counter()},
                'podcast': {'authors': Counter(), 'genres': Counter()}}
    seen = set()
    for source in rows:
        require(isinstance(source, dict)
                and source.get('media_type') in affinity
                and isinstance(source.get('authority_id'), str)
                and source['authority_id'] not in seen,
                'books-landing-item')
        seen.add(source['authority_id'])
        authors = _tokens(source.get('_authors', []), 40, 'books-landing-authors')
        genres = _tokens(source.get('_genres', []), 40, 'books-landing-genres')
        progress = _progress(source.get('_progress'))
        if progress is not None and not progress[3] and (progress[1] > 0 or progress[2]):
            weight = 4 if progress[2] else max(1, min(3, int(progress[1] / max(progress[0], 1) * 4) + 1))
            affinity[source['media_type']]['authors'].update(
                {item.casefold(): weight for item in authors})
            affinity[source['media_type']]['genres'].update(
                {item.casefold(): weight for item in genres})
        prepared.append((source, authors, genres, progress))

    output = []
    for source, authors, genres, progress in prepared:
        row = {key: value for key, value in source.items() if not key.startswith('_')}
        row.pop('recommendation_score', None)
        row.pop('recommendation_reason', None)
        if progress is None:
            values = affinity[source['media_type']]
            author_matches = sorted(
                ((values['authors'][item.casefold()], item) for item in authors
                 if values['authors'][item.casefold()]), reverse=True)
            genre_matches = sorted(
                ((values['genres'][item.casefold()], item) for item in genres
                 if values['genres'][item.casefold()]), reverse=True)
            if author_matches:
                weight, label = author_matches[0]
                row['recommendation_score'] = min(100.0, 68.0 + weight * 7)
                row['recommendation_reason'] = 'Because you listen to ' + label
            elif genre_matches:
                weight, label = genre_matches[0]
                row['recommendation_score'] = min(100.0, 48.0 + weight * 8)
                row['recommendation_reason'] = 'Because you listen to ' + label
        output.append(row)
    return output


def landing_rows(records, cover):
    """Map the sanitized catalogue into the shared owned-landing contract."""
    require(isinstance(records, list) and len(records) <= 1000 and callable(cover),
            'books-landing-records')
    rows = []
    for record in records:
        require(isinstance(record, dict), 'books-landing-record')
        artwork = cover(record) or ''
        rows.append({
            'identity': ({'ebook': 'calibre:', 'audiobook': 'audiobookshelf:',
                          'podcast': 'audiobookshelf:'}[record['kind']] + record['id']),
            'media_type': record['kind'], 'title': record['title'],
            'detail': record['detail'], 'synopsis': record.get('synopsis', ''),
            'artwork': artwork, 'backdrop': artwork,
            'added_at': record.get('added_at'),
            'recommendation_score': record.get('recommendation_score'),
            'recommendation_reason': record.get('recommendation_reason', ''),
        })
    return rows
