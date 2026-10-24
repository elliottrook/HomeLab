"""Read-only series-page preparation. No Kodi imports, streams or playback writes.

The existing v1.1 Up Next adapter supplies next_episode_id; this module never
infers a future episode or replaces that adapter's sequencing policy.
"""
from dataclasses import dataclass
from datetime import date
import math

_NO_SEASON=object()


class SeriesUnavailable(ValueError):
    pass


def _id(value):
    return type(value) is int and 0 < value <= 2147483647


def _number(value):
    return value if type(value) is int and value >= 0 else None


def _seconds(value):
    if type(value) not in (int, float):
        return None
    try:value=float(value)
    except (OverflowError,ValueError):return None
    if not math.isfinite(value) or value < 0:
        return None
    return value


@dataclass(frozen=True)
class Episode:
    episode_id: int
    season: object
    number: object
    title: str
    synopsis: str
    thumbnail: str
    duration: object
    first_aired: str
    available: bool
    watched: bool
    resume_seconds: object
    progress_percent: object
    last_played: str

    @property
    def numbering(self):
        if self.season is None or self.number is None:
            return 'Episode number unavailable'
        return f'S{self.season} E{self.number}'


@dataclass(frozen=True)
class Season:
    number: object
    label: str
    episodes: tuple


@dataclass(frozen=True)
class SeriesPage:
    show_id: int
    seasons: tuple
    primary_episode_id: object
    primary_action: str

    @property
    def show_season_picker(self):
        return len(self.seasons) > 1

    def restore(self, episode_id=None, season=_NO_SEASON):
        """Exact ID survives reorder; fall back within the remembered season.

        Returns a season index and episode index, never a guessed playable ID.
        Empty pages return None so the eventual view can focus Back instead.
        """
        if _id(episode_id):
            for s, group in enumerate(self.seasons):
                for e, row in enumerate(group.episodes):
                    if row.episode_id == episode_id:
                        return s, e
        for s, group in enumerate(self.seasons):
            if group.number == season:
                return s, 0
        return (0, 0) if self.seasons else None


def build_series(show_id, records, *, expected_total, next_episode_id=None, today=None):
    """Require a complete same-show snapshot, preserve unknown facts explicitly.

    Availability means an indexed nonempty source and no known future air date;
    it is not proof a remote stream is online. Stream resolution stays in the
    existing player. Raw paths are inspected but never retained in this model.
    """
    if not _id(show_id) or not isinstance(records, list):
        raise SeriesUnavailable('invalid-series-snapshot')
    if type(expected_total) is not int or expected_total != len(records):
        raise SeriesUnavailable('incomplete-series-snapshot')
    today = date.fromisoformat(today) if today is not None else date.today()
    rows=[];seen=set()
    for source in records:
        if (not isinstance(source,dict) or not _id(source.get('episodeid'))
                or type(source.get('tvshowid')) is not int or source['tvshowid']!=show_id):
            raise SeriesUnavailable('invalid-episode-identity')
        identity=source['episodeid']
        if identity in seen:
            raise SeriesUnavailable('duplicate-episode-identity')
        seen.add(identity)
        aired=source.get('firstaired') or ''
        if not isinstance(aired,str):
            raise SeriesUnavailable('invalid-air-date')
        try:air_date=date.fromisoformat(aired) if aired else None
        except ValueError:raise SeriesUnavailable('invalid-air-date') from None
        path=source.get('file');available=isinstance(path,str) and bool(path.strip()) and (air_date is None or air_date<=today)
        resume=source.get('resume') if isinstance(source.get('resume'),dict) else {}
        position=_seconds(resume.get('position'));total=_seconds(resume.get('total'))
        valid_resume=(position is not None and total is not None and 0<position<total)
        playcount=source.get('playcount',0)
        if type(playcount) is not int or playcount<0:
            raise SeriesUnavailable('invalid-watch-state')
        art=source.get('art') if isinstance(source.get('art'),dict) else {}
        text=lambda key,default='':source.get(key) if isinstance(source.get(key),str) and source[key] else default
        duration=_seconds(source.get('runtime'))
        rows.append(Episode(identity,_number(source.get('season')),_number(source.get('episode')),
            text('title',text('label','Untitled episode')),text('plot'),
            art.get('thumb') if isinstance(art.get('thumb'),str) else '',
            duration if duration else None,aired,available,playcount>0,
            position if valid_resume else None,position/total*100 if valid_resume else None,text('lastplayed')))
    rows.sort(key=lambda row:(row.season is None,row.season or 0,row.number is None,row.number or 0,row.episode_id))
    numbers=sorted({row.season for row in rows if row.season is not None and row.season>0})
    if any(row.season==0 for row in rows):numbers.append(0)
    if any(row.season is None for row in rows):numbers.append(None)
    groups=tuple(Season(number,'Specials' if number==0 else 'Other episodes' if number is None else f'Season {number}',
        tuple(row for row in rows if row.season==number)) for number in numbers)
    primary=None;action='browse'
    resumed=[row for row in rows if row.available and row.resume_seconds is not None]
    if resumed:
        primary=max(resumed,key=lambda row:(row.last_played,row.episode_id)).episode_id;action='resume'
    elif next_episode_id is not None:
        if not _id(next_episode_id):raise SeriesUnavailable('invalid-next-episode')
        candidate=next((row for row in rows if row.episode_id==next_episode_id),None)
        if candidate and candidate.available and not candidate.watched and candidate.season and candidate.number:
            primary=candidate.episode_id;action='next'
    elif not any(row.watched for row in rows if row.season and row.number):
        regular=[row for row in rows if row.season and row.number]
        # Do not skip an unavailable first indexed regular episode.
        if regular and regular[0].available:
            primary=regular[0].episode_id;action='play'
    return SeriesPage(show_id,groups,primary,action)
