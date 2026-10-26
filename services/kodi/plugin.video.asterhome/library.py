"""Pure helpers for Aster's read-only combined video library views."""

from datetime import date
import math

GENRES = {
    'Comedy': ('comedy',),
    'Drama': ('drama',),
    'Action': ('action',),
    'Sci-Fi': ('sci-fi', 'science fiction'),
    'Documentary': ('documentary',),
    'Horror': ('horror',),
    'Family': ('family',),
}


def canonical_genre(value):
    """Return an allowed display genre or None for an untrusted value."""
    candidate = (value or '').strip().casefold()
    return next((name for name in GENRES if name.casefold() == candidate), None)


def matches_genre(item, genre):
    """Match Kodi's list of genre labels, including common Sci-Fi spelling."""
    tokens = GENRES[genre]
    values = item.get('genre', [])
    if not isinstance(values, list):
        return False
    return any(token in str(value).casefold() for value in values for token in tokens)


def combined_items(movies, shows, genre):
    """Merge matching movie and TV-show rows without changing source records."""
    result = []
    for kind, identifier, rows in (('movie', 'movieid', movies),
                                   ('tvshow', 'tvshowid', shows)):
        if not isinstance(rows, list):
            continue
        for source in rows:
            if not isinstance(source, dict) or identifier not in source:
                continue
            if matches_genre(source, genre):
                row = dict(source)
                row['kind'] = kind
                row['id'] = source[identifier]
                row['label'] = source.get('label') or source.get('title') or 'Untitled'
                result.append(row)
    return sorted(result, key=lambda row: (row['label'].casefold(), row['kind']))


def recent_items(movies, shows, limit=24):
    """Merge newly added movies and series without allowing one show to flood a rail."""
    result = []
    for kind, identifier, rows in (('movie', 'movieid', movies),
                                   ('tvshow', 'tvshowid', shows)):
        if not isinstance(rows, list):
            continue
        for source in rows:
            if not isinstance(source, dict) or type(source.get(identifier)) is not int:
                continue
            added = source.get('dateadded')
            if not isinstance(added, str) or not added.strip():
                continue
            row = dict(source)
            row.update(kind=kind, id=source[identifier],
                       label=source.get('label') or source.get('title') or 'Untitled')
            result.append(row)
    result.sort(key=lambda row: (row['dateadded'], row['label'].casefold()),
                reverse=True)
    return result[:max(0, int(limit))]


def recommended_items(movies, shows, limit=12, recent_exclusion=12):
    """Rank only playable/browsable local titles for the idle media hero.

    Recommendations are derived from Kodi's local library metadata.  The
    acquisition catalogue is intentionally not an input: an item shown with a
    Play/Browse action must already be owned and indexed on this box.
    """
    sources = []
    affinity = {}
    for kind, identifier, rows in (('movie', 'movieid', movies),
                                   ('tvshow', 'tvshowid', shows)):
        if not isinstance(rows, list):
            continue
        for source in rows:
            if not isinstance(source, dict) or type(source.get(identifier)) is not int:
                continue
            genres = source.get('genre', [])
            genres = genres if isinstance(genres, list) else []
            watched = (source.get('playcount', 0) > 0 if kind == 'movie'
                       else source.get('watchedepisodes', 0) > 0)
            if watched:
                for genre in genres:
                    token = str(genre).strip().casefold()
                    if token:
                        affinity[token] = affinity.get(token, 0) + 1
            row = dict(source)
            row.update(kind=kind, id=source[identifier],
                       label=source.get('label') or source.get('title') or 'Untitled')
            sources.append(row)

    recent = sorted((row for row in sources if row.get('dateadded')),
                    key=lambda row: (row['dateadded'], row['label'].casefold()),
                    reverse=True)
    excluded = {(row['kind'], row['id'])
                for row in recent[:max(0, int(recent_exclusion))]}

    candidates = []
    for row in sources:
        if (row['kind'], row['id']) in excluded:
            continue
        art = row.get('art') if isinstance(row.get('art'), dict) else {}
        if not (art.get('fanart') or art.get('tvshow.fanart')):
            continue
        if row['kind'] == 'movie':
            if row.get('playcount', 0) > 0 or not str(row.get('file') or '').strip():
                continue
        elif row.get('unwatchedepisodes', 0) <= 0:
            continue
        genres = row.get('genre', [])
        genres = genres if isinstance(genres, list) else []
        genre_score = sum(affinity.get(str(genre).strip().casefold(), 0)
                          for genre in genres)
        try:
            rating = float(row.get('rating') or 0)
            if not math.isfinite(rating):
                rating = 0.0
        except (TypeError, ValueError):
            rating = 0.0
        row['_recommendation_score'] = (genre_score, rating,
                                        row.get('dateadded') or '')
        candidates.append(row)
    candidates.sort(key=lambda row: (row['_recommendation_score'],
                                      row['label'].casefold()), reverse=True)
    for row in candidates:
        row.pop('_recommendation_score', None)
    return candidates[:max(0, int(limit))]


def continue_items(movies, episodes, limit=24):
    """Merge resumable movies and episodes in most-recently-played order."""
    result = []
    for kind, rows in (('movie', movies), ('episode', episodes)):
        if not isinstance(rows, list):
            continue
        for source in rows:
            if not isinstance(source, dict):
                continue
            resume = source.get('resume')
            if not isinstance(resume, dict):
                continue
            try:
                position = float(resume.get('position', 0))
                total = float(resume.get('total', 0))
            except (TypeError, ValueError):
                continue
            if not math.isfinite(position) or not math.isfinite(total) or position <= 0 or total <= 0 or position >= total:
                continue
            row = dict(source)
            row['kind'] = kind
            row['label'] = source.get('label') or source.get('title') or 'Untitled'
            row['resume_position'] = position
            row['resume_total'] = total
            result.append(row)
    result.sort(key=lambda row: (row.get('lastplayed') or '', row['label'].casefold()),
                reverse=True)
    return result[:limit]


def next_up_item(show, episodes, today=None):
    """One available next episode for a previously watched show, or nothing.

    The caller supplies a complete, locally synced season/episode catalogue.
    Specials and episode-zero extras do not advance regular-season ordering.
    Never mark watched, invent an air date, or return a guessed stream URL.
    """
    today = today or date.today().isoformat()
    rows = [row for row in episodes if isinstance(row, dict)
            and type(row.get('season')) is int and row['season'] > 0
            and type(row.get('episode')) is int and row['episode'] > 0]
    watched = [row for row in rows if row.get('playcount', 0) > 0]
    if not watched:
        return None
    order = lambda row: (row['season'], row['episode'])
    last = max(watched, key=order)
    later = sorted((row for row in rows if order(row) > order(last)
                    and not row.get('playcount', 0)), key=order)
    recent = max((row.get('lastplayed') or '' for row in watched), default='')
    if later:
        episode = later[0]
        # A missing episode is not permission to jump forward over it.
        sequential = ((episode['season'] == last['season']
                       and episode['episode'] == last['episode'] + 1)
                      or (episode['season'] == last['season'] + 1
                          and episode['episode'] == 1))
        aired = episode.get('firstaired') or ''
        path = episode.get('file')
        if sequential and isinstance(path, str) and path.strip() and (not aired or aired[:10] <= today):
            row = dict(episode)
            row.update(kind='episode', resume_position=0, resume_total=0,
                       lastplayed=recent, next_up=True,
                       label=f"Up next · {episode.get('showtitle') or show.get('label', 'Series')}"
                             f" — S{episode['season']} E{episode['episode']}")
            return row
    return None


def watching_items(movies, episodes, shows, episodes_by_show, limit=24, today=None):
    """Keep genuine resume points; fill recently watched series with Up Next."""
    result = continue_items(movies, episodes, limit=100)
    resuming = {row.get('tvshowid') for row in result if row['kind'] == 'episode'}
    seen = set()
    for show in shows:
        identity = show.get('tvshowid')
        if identity is None or identity in resuming or identity in seen:
            continue
        seen.add(identity)
        if identity not in episodes_by_show:
            continue  # A failed/truncated query is not evidence of being caught up.
        row = next_up_item(show, episodes_by_show[identity], today)
        if row:
            result.append(row)
    result.sort(key=lambda row: (row.get('lastplayed') or '', row['label'].casefold()),
                reverse=True)
    return result[:limit]
