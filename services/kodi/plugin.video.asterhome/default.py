"""Read-only combined Kodi-library directories for Aster Home."""

import json
import sys
import traceback
from urllib.parse import parse_qs

import xbmc
import xbmcgui
import xbmcplugin

from library import (canonical_genre, combined_items, recent_items,
                     recommendation_exclusions, recommended_items, watching_items)


PROPERTIES = ['title', 'plot', 'year', 'genre', 'rating', 'mpaa', 'art', 'file']
CONTINUE_PROPERTIES = PROPERTIES + [
    'lastplayed', 'resume', 'runtime', 'playcount',
]
EPISODE_PROPERTIES = [
    'title', 'plot', 'rating', 'art', 'file', 'lastplayed', 'resume',
    'runtime', 'playcount', 'showtitle', 'season', 'episode', 'tvshowid', 'firstaired',
]
RECENT_PROPERTIES = PROPERTIES + ['dateadded']
MOVIE_RECOMMEND_PROPERTIES = RECENT_PROPERTIES + ['playcount', 'resume']
SHOW_RECOMMEND_PROPERTIES = RECENT_PROPERTIES + [
    'episode', 'watchedepisodes',
]
RECOMMEND_EPISODE_PROPERTIES = ['tvshowid', 'resume']


def rpc(method, properties=PROPERTIES, sort=None, filter_value=None, limits=None, **extra):
    request = {
        'jsonrpc': '2.0', 'id': 1, 'method': method,
        'params': {'properties': properties,
                   'sort': sort or {'method': 'title', 'order': 'ascending'}},
    }
    if filter_value is not None:
        request['params']['filter'] = filter_value
    if limits is not None:
        request['params']['limits'] = limits
    request['params'].update(extra)
    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if 'error' in response:
        raise ValueError(response['error'].get('message', 'Kodi library query failed'))
    return response.get('result', {})


def all_episodes(properties, page_size=2000, maximum=20000):
    """Read a complete bounded episode projection without trusting truncation."""
    rows = []
    while True:
        result = rpc('VideoLibrary.GetEpisodes', properties,
                     limits={'start': len(rows), 'end': len(rows) + page_size})
        batch = result.get('episodes', [])
        total = result.get('limits', {}).get('total', len(rows) + len(batch))
        if (not isinstance(batch, list) or type(total) is not int or total < 0
                or total > maximum or len(rows) + len(batch) > maximum):
            raise ValueError('Episode catalogue exceeds recommendation exclusion bound')
        rows.extend(batch)
        if len(rows) >= total:
            return rows
        if not batch:
            raise ValueError('Episode catalogue pagination stalled')


def add_item(handle, row):
    item = xbmcgui.ListItem(label=row['label'])
    item.setProperty('AsterMediaKind', row['kind'])
    if row.get('next_up'):
        item.setProperty('AsterUpNext', 'true')
    item.setInfo('video', {
        'title': row['label'], 'plot': row.get('plot', ''),
        'year': row.get('year', 0), 'genre': row.get('genre', []),
        'rating': row.get('rating', 0), 'mpaa': row.get('mpaa', ''),
        'mediatype': row['kind'], 'duration': row.get('runtime', 0),
        'tvshowtitle': row.get('showtitle', ''),
        'season': row.get('season', 0), 'episode': row.get('episode', 0),
    })
    art = row.get('art') if isinstance(row.get('art'), dict) else {}
    if art:
        item.setArt(art)
    if row.get('resume_position', 0) > 0:
        item.getVideoInfoTag().setResumePoint(
            row['resume_position'], row.get('resume_total', 0))
    if row['kind'] == 'episode' and type(row.get('episodeid')) is int:
        item.getVideoInfoTag().setDbId(row['episodeid'])
    if row['kind'] == 'tvshow':
        if type(row.get('id')) is int:
            item.getVideoInfoTag().setDbId(row['id'])
            item.setProperty('AsterDbId', str(row['id']))
        url = f"videodb://tvshows/titles/{row['id']}/"
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=True)
        return
    url = row.get('file', '')
    item.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)


def add_continue_watching(handle):
    latest = {'method': 'lastplayed', 'order': 'descending'}
    # Kodi 21 rejects the documented ``inprogress`` JSON-RPC filter on some
    # library providers. Fetch the recently played candidates and let
    # watching_items() validates resume points and adds locally synced Up Next.
    limits = {'start': 0, 'end': 100}
    movie_result = rpc('VideoLibrary.GetMovies', CONTINUE_PROPERTIES,
                       latest, limits=limits)
    episode_result = rpc('VideoLibrary.GetEpisodes', EPISODE_PROPERTIES,
                         latest, limits=limits)
    shows, episodes_by_show = [], {}
    try:
        show_result = rpc('VideoLibrary.GetTVShows',
                          PROPERTIES + ['lastplayed', 'watchedepisodes'],
                          latest, limits={'start': 0, 'end': 1000})
        shows = show_result.get('tvshows', [])
        if show_result.get('limits', {}).get('total', len(shows)) > len(shows):
            raise ValueError('Series catalogue exceeds complete-read bound')
        for show in shows:
            if not show.get('watchedepisodes', 0):
                continue
            identity = show['tvshowid']
            result = rpc('VideoLibrary.GetEpisodes', EPISODE_PROPERTIES,
                         limits={'start': 0, 'end': 2000}, tvshowid=identity)
            episodes = result.get('episodes', [])
            if result.get('limits', {}).get('total', len(episodes)) <= len(episodes):
                episodes_by_show[identity] = episodes
    except (KeyError, TypeError, ValueError):
        # Keep resume working if the optional next-episode query fails.
        xbmc.log('Aster Up Next: local series catalogue unavailable; keeping resume items.',
                 xbmc.LOGWARNING)
    rows = watching_items(movie_result.get('movies', []),
                          episode_result.get('episodes', []), shows, episodes_by_show)
    xbmcplugin.setPluginCategory(handle, 'Continue Watching')
    xbmcplugin.setContent(handle, 'videos')
    for row in rows:
        add_item(handle, row)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def add_recently_added(handle):
    latest = {'method': 'dateadded', 'order': 'descending'}
    limits = {'start': 0, 'end': 100}
    movie_result = rpc('VideoLibrary.GetMovies', RECENT_PROPERTIES,
                       latest, limits=limits)
    show_result = rpc('VideoLibrary.GetTVShows', RECENT_PROPERTIES,
                      latest, limits=limits)
    rows = recent_items(movie_result.get('movies', []),
                        show_result.get('tvshows', []))
    xbmcplugin.setPluginCategory(handle, 'Recently Added')
    xbmcplugin.setContent(handle, 'videos')
    for row in rows:
        add_item(handle, row)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def add_recommended(handle):
    limits = {'start': 0, 'end': 2000}
    movie_result = rpc('VideoLibrary.GetMovies', MOVIE_RECOMMEND_PROPERTIES,
                       limits=limits)
    show_result = rpc('VideoLibrary.GetTVShows', SHOW_RECOMMEND_PROPERTIES,
                      limits=limits)
    episodes = all_episodes(RECOMMEND_EPISODE_PROPERTIES)
    excluded_movies, excluded_shows = recommendation_exclusions(
        movie_result.get('movies', []), episodes,
        show_result.get('tvshows', []))
    rows = recommended_items(movie_result.get('movies', []),
                             show_result.get('tvshows', []),
                             excluded_movies=excluded_movies,
                             excluded_shows=excluded_shows)
    xbmcplugin.setPluginCategory(handle, 'Recommended for You')
    xbmcplugin.setContent(handle, 'videos')
    for row in rows:
        add_item(handle, row)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def rotate_hero():
    """Advance the idle recommendation without taking remote focus."""
    if xbmcgui.getCurrentWindowId() != 10000:
        return
    focus = xbmcgui.Window(10000).getFocusId()
    if focus not in (100, 110):
        xbmc.executebuiltin('Control.Move(101,1)')


def main():
    handle = int(sys.argv[1])
    query = parse_qs(sys.argv[2].lstrip('?'))
    if query.get('mode', [''])[0] == 'continue':
        try:
            add_continue_watching(handle)
        except Exception as error:  # Kodi surfaces only a generic directory error.
            xbmc.log(f'Aster Media Continue Watching: {error}\n{traceback.format_exc()}',
                     xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Aster Media',
                                          'Continue Watching could not be refreshed.')
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
        return
    if query.get('mode', [''])[0] == 'recent':
        try:
            add_recently_added(handle)
        except Exception as error:
            xbmc.log(f'Aster Media Recently Added: {error}\n{traceback.format_exc()}',
                     xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Aster Media',
                                          'Recently Added could not be refreshed.')
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
        return
    if query.get('mode', [''])[0] == 'recommended':
        try:
            add_recommended(handle)
        except Exception as error:
            xbmc.log(f'Aster Media Recommendations: {error}\n{traceback.format_exc()}',
                     xbmc.LOGERROR)
            xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
        return
    genre = canonical_genre(query.get('genre', [''])[0])
    if genre is None:
        xbmcgui.Dialog().ok('Aster Media', 'Choose a supported genre from the Aster Media page.')
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    try:
        movie_result = rpc('VideoLibrary.GetMovies')
        show_result = rpc('VideoLibrary.GetTVShows')
        rows = combined_items(movie_result.get('movies', []),
                              show_result.get('tvshows', []), genre)
    except (TypeError, ValueError, json.JSONDecodeError):
        xbmcgui.Dialog().ok('Aster Media', 'Kodi could not read the local video library.')
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    xbmcplugin.setPluginCategory(handle, f'{genre} · Movies & TV')
    xbmcplugin.setContent(handle, 'videos')
    for row in rows:
        add_item(handle, row)
    if not rows:
        xbmcgui.Dialog().notification('Aster Media', f'No {genre} movies or TV shows found.')
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'hero-tick':
        rotate_hero()
    else:
        main()
