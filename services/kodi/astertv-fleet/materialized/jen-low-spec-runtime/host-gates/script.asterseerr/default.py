"""AsterTV Seerr request page; broker-only, explicit writes, no playback."""
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'resources/lib'))
from seerr_broker_client import BrokerUnavailable, RequestWriter
from seerr_page_model import (Page, PageUnavailable, action_label, complete,
                              load, request, requestable, select,
                              toggle_season)

PREFIX = 'AsterSeerr.'

def window_active(window_id):
    return (xbmcgui.getCurrentWindowId() == window_id or
            xbmc.getCondVisibility('Window.IsActive(' + str(window_id) + ')'))

BROKER = 'http://192.168.20.40:8788'
TOKEN = Path('/storage/.aster-private/seerr-token')
JOURNAL = Path('/storage/.aster-private/seerr-journal')


def broker(method, path, body=None):
    token = TOKEN.read_text().strip()
    if not 32 <= len(token) <= 512 or not path.startswith('/v1/'):
        raise BrokerUnavailable('seerr-broker-configuration-invalid')
    encoded = None if body is None else json.dumps(body, separators=(',', ':')).encode()
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    if encoded is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(BROKER + path, data=encoded, method=method,
                                     headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(65537)
            if response.status != 200 or len(raw) > 65536:
                raise BrokerUnavailable('seerr-broker-response-invalid')
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError
            return value
    except (OSError, urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, ValueError) as error:
        raise BrokerUnavailable('seerr-broker-unavailable') from error


def main():
    if os.uname().nodename not in ('AsterTV-Bedroom', 'AsterTV-Family', 'AsterTV-Jen'):
        return
    home = xbmcgui.Window(10000)
    page = Page()
    media_type = 'all'
    # Acquisition Hub may pass a selected media recommendation. Consume the
    # bounded, non-secret seed once so later visits open a normal empty page.
    query = ' '.join(home.getProperty(PREFIX + 'QuerySeed').split())[:100]
    seeded_type = home.getProperty(PREFIX + 'TypeSeed')
    if seeded_type in ('all', 'movie', 'tv'):
        media_type = seeded_type
    home.clearProperty(PREFIX + 'QuerySeed')
    home.clearProperty(PREFIX + 'TypeSeed')
    opened = False
    details_active = False
    monitor = xbmc.Monitor()

    def prop(name, value=''):
        home.setProperty(PREFIX + name, str(value)) if value != '' else home.clearProperty(PREFIX + name)

    def render():
        item = page.item
        prop('DetailsActive', 'true' if details_active else 'false')
        prop('Query', query or 'Search Seerr…')
        prop('Status', page.status)
        prop('Filter', {'all': 'All', 'movie': 'Films', 'tv': 'Television'}[media_type])
        if not item:
            for key in ('Title', 'Metadata', 'Synopsis', 'Backdrop', 'Poster',
                        'RequestLabel', 'SeasonHint'):
                prop(key)
            prop('SeasonsVisible', 'false')
            return
        prop('Title', item.title)
        prop('Metadata', ('Film' if item.media_type == 'movie' else 'Television') +
             (' · ' + item.year if item.year else '') + ' · ' + item.availability.replace('_', ' ').title())
        prop('Synopsis', item.overview or 'No synopsis is available.')
        prop('Backdrop', item.backdrop)
        prop('Poster', item.poster)
        prop('RequestLabel', action_label(page))
        seasons_visible = item.media_type == 'tv' and requestable(item)
        prop('SeasonsVisible', 'true' if seasons_visible else 'false')
        prop('SeasonHint', (str(len(page.seasons)) + ' selected' if page.seasons
                           else 'Choose one or more seasons') if seasons_visible else '')

    def fill_results():
        control = window.getControl(30)
        control.reset()
        for item in page.candidates:
            row = xbmcgui.ListItem(label=item.title, label2=item.year)
            row.setArt({'thumb': item.poster, 'poster': item.poster})
            row.setProperty('Kind', 'Film' if item.media_type == 'movie' else 'TV')
            row.setProperty('State', item.availability.replace('_', ' ').title())
            control.addItem(row)
        if page.selected >= 0:
            control.selectItem(page.selected)

    def fill_seasons(selected_position=0):
        control = window.getControl(40)
        control.reset()
        item = page.item
        if item and item.media_type == 'tv':
            for season in item.seasons:
                checked = season in page.seasons
                row = xbmcgui.ListItem(label=('✓  ' if checked else '○  ') + 'Season ' + str(season))
                row.setProperty('Season', str(season))
                control.addItem(row)
            if item.seasons:
                control.selectItem(min(max(selected_position, 0), len(item.seasons) - 1))

    def search_now():
        nonlocal page, details_active
        details_active = False
        prop('Status', 'Searching Seerr…')
        path = '/v1/search?' + urllib.parse.urlencode({'q': query, 'type': media_type})
        page = load(broker('GET', path), query)
        fill_results(); fill_seasons(0); render()

    try:
        if not TOKEN.is_file() or TOKEN.is_symlink():
            raise BrokerUnavailable('seerr-broker-not-configured')
        # Search is a modal window on this Kodi build.  Close it from inside
        # the addon before opening Requests; chaining two builtins in the XML
        # onclick is parsed as one malformed window command.
        xbmc.executebuiltin('Dialog.Close(11127)')
        deadline = time.monotonic() + 2
        while xbmcgui.getCurrentWindowDialogId() == 11127:
            if time.monotonic() >= deadline or monitor.waitForAbort(.05):
                raise BrokerUnavailable('search-window-will-not-close')
        xbmc.executebuiltin('ActivateWindow(1132)')
        opened = True
        deadline = time.monotonic() + 5
        while not window_active(11132):
            if time.monotonic() >= deadline or monitor.waitForAbort(.05):
                raise BrokerUnavailable('seerr-window-unavailable')
        window = xbmcgui.Window(11132)
        results = window.getControl(30)
        render()
        if query:
            search_now()
        selected = -1
        writer = RequestWriter(JOURNAL, lambda payload: broker('POST', '/v1/request', payload))
        while window_active(11132) and not monitor.abortRequested():
            command = home.getProperty(PREFIX + 'Command')
            if command:
                home.clearProperty(PREFIX + 'Command')
                try:
                    if command == 'back':
                        if details_active:
                            details_active = False
                            render(); window.setFocusId(30)
                        else:
                            xbmc.executebuiltin('ActivateWindow(Home)'); break
                    if command == 'search':
                        keyboard = xbmc.Keyboard(query, 'Search films and television')
                        keyboard.doModal()
                        if keyboard.isConfirmed():
                            query = ' '.join(keyboard.getText().split())[:100]
                            if query:
                                search_now()
                    elif command.startswith('filter:'):
                        value = command.split(':', 1)[1]
                        if value in ('all', 'movie', 'tv'):
                            media_type = value
                            if query:
                                search_now()
                            else:
                                render()
                    elif command == 'details' and page.item:
                        details_active = True
                        render()
                        window.setFocusId(40 if page.item.media_type == 'tv' else 50)
                    elif command == 'season' and page.item:
                        position = window.getControl(40).getSelectedPosition()
                        if 0 <= position < len(page.item.seasons):
                            page = toggle_season(page, page.item.seasons[position])
                            seasons = window.getControl(40)
                            for row_index, season in enumerate(page.item.seasons):
                                checked = season in page.seasons
                                seasons.getListItem(row_index).setLabel(
                                    ('✓  ' if checked else '○  ') + 'Season ' + str(season))
                            seasons.selectItem(position)
                            window.setFocusId(40)
                            render()
                    elif command == 'request' and page.item:
                        page, proposal = request(page, page.phase == 'confirm')
                        render()
                        if proposal.state == 'ready':
                            page = complete(page, writer.submit(proposal))
                            render()
                except (PageUnavailable, BrokerUnavailable, ValueError, OSError):
                    page = Page(query=query, candidates=page.candidates,
                                selected=page.selected, seasons=page.seasons,
                                phase='error', status='Request service unavailable · nothing was retried')
                    render()
            position = results.getSelectedPosition()
            if 0 <= position < len(page.candidates) and position != selected:
                page = select(page, position)
                selected = position
                details_active = False
                fill_seasons(0); render()
            if monitor.waitForAbort(.05):
                break
    except (BrokerUnavailable, OSError):
        xbmcgui.Dialog().notification('Requests unavailable',
                                      'The private Seerr broker is not ready.')
    finally:
        for key in ('Command', 'Query', 'Status', 'Filter', 'Title', 'Metadata',
                    'Synopsis', 'Backdrop', 'Poster', 'RequestLabel',
                    'SeasonHint', 'SeasonsVisible', 'DetailsActive'):
            home.clearProperty(PREFIX + key)
        if opened and window_active(11132):
            xbmc.executebuiltin('ActivateWindow(Home)')


if __name__ == '__main__':
    main()
