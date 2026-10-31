"""Make the G20 OK button activate Aster's script-populated list items.

Kodi activates native library paths when Select is pressed, but the rows that
Aster fills through ``xbmcgui.ControlList.addItems`` have no safe media path to
open directly. The list-level ``onclick`` is not dispatched for those rows on
LibreELEC/Kodi 21. Route only known custom-window list controls to their
existing bounded handlers and preserve normal Select everywhere else.
"""


MUSIC_WINDOWS = {
    11113: 'home',
    11114: 'albums',
    11115: 'artists',
    11116: 'songs',
    11117: 'playlists',
}
BOOK_WINDOWS = {
    11110: ('home', {501, 502, 503}),
    11118: ('ebooks', {500}),
    11119: ('audiobooks', {500}),
    11120: ('podcasts', {500}),
}


SERIES_CONTROLS = frozenset((200, 201, 202, 300, 311, 312, 313, 314, 315))


DYNAMIC_CONTROLS = {
    **{window_id: frozenset((500,)) for window_id in MUSIC_WINDOWS},
    **{window_id: frozenset(controls) for window_id, (_, controls) in BOOK_WINDOWS.items()},
    11111: frozenset((500,)),
    11121: frozenset((50,)),
    11127: frozenset((30, 51)),
    11129: frozenset((30,)),
    11132: frozenset((30, 40)),
    11133: frozenset((30,)),
}


def active_window_id(xbmc, xbmcgui):
    """Resolve a custom window even when Kodi reports its base-window ID."""
    reported = xbmcgui.getCurrentWindowId()
    if reported in DYNAMIC_CONTROLS:
        return reported
    for window_id in DYNAMIC_CONTROLS:
        if xbmc.getCondVisibility('Window.IsActive(' + str(window_id) + ')'):
            return window_id
    return reported


def focused_control_id(xbmc, xbmcgui, window_id):
    """Use the skin focus state when Kodi's Python Window wrapper returns 0."""
    try:
        reported = xbmcgui.Window(window_id).getFocusId()
    except RuntimeError:
        reported = 0
    controls = DYNAMIC_CONTROLS.get(window_id, ())
    if reported in controls:
        return reported
    for control_id in controls:
        if xbmc.getCondVisibility('Control.HasFocus(' + str(control_id) + ')'):
            return control_id
    return reported


def series_command_target(identity, visible, focus_id):
    """Return the verified scripted-window identity for an OK command."""
    if (not isinstance(identity, str) or not identity.isdecimal()
            or not visible or focus_id not in SERIES_CONTROLS):
        return None
    value = int(identity)
    return value if 12000 <= value <= 13999 else None


def dispatched_action(window_id, focus_id):
    """Return a trusted built-in for an Aster dynamic list, or ``None``."""
    if window_id == 11127 and focus_id == 51:
        return 'RunScript(script.asterseerr)'
    if window_id in MUSIC_WINDOWS and focus_id == 500:
        return ('RunScript(special://skin/tools/music_data.py,'
                + MUSIC_WINDOWS[window_id] + ',open)')
    if window_id in BOOK_WINDOWS:
        page, controls = BOOK_WINDOWS[window_id]
        if focus_id in controls:
            return ('RunScript(special://skin/tools/books_data.py,'
                    + page + ',activate)')
    if window_id == 11111 and focus_id == 500:
        return 'RunScript(special://skin/tools/hub_data.py,digest,chapter)'
    if window_id == 11121 and focus_id == 50:
        return 'RunScript(special://skin/tools/music_data.py,music-player,track)'
    if window_id == 11132 and focus_id == 30:
        return 'SetProperty(AsterSeerr.Command,details,home)'
    if window_id == 11133 and focus_id == 30:
        return 'SetProperty(AsterAcquisition.Command,action,home)'
    if window_id == 11132 and focus_id == 40:
        return 'SetProperty(AsterSeerr.Command,season,home)'
    return None


def main():
    import xbmc
    import xbmcgui

    window_id = active_window_id(xbmc, xbmcgui)
    focus_id = focused_control_id(xbmc, xbmcgui, window_id)
    xbmc.log('AsterSelect: entered window=' + str(window_id)
             + ' focus=' + str(focus_id), xbmc.LOGINFO)

    # Script-populated Aster controls must win over stale global properties.
    # In particular, AsterSeries.PreviewWindow can survive after leaving TV and
    # used to swallow KEY_SELECT on Books, Podcasts and Music without a trace.
    action = dispatched_action(window_id, focus_id)
    if action is not None:
        xbmc.log('AsterSelect: dispatch action=' + action, xbmc.LOGINFO)
        xbmc.executebuiltin(action)
        return

    home = xbmcgui.Window(10000)
    series_identity = home.getProperty('AsterSeries.PreviewWindow')
    if series_identity.isdecimal():
        value = int(series_identity)
        visible = xbmc.getCondVisibility('Window.IsVisible(' + series_identity + ')')
        try:
            series_focus = xbmcgui.Window(value).getFocusId()
        except RuntimeError:
            series_focus = 0
        target = series_command_target(series_identity, visible, series_focus)
        if target is not None:
            xbmc.log('AsterSelect: series target=' + str(target), xbmc.LOGINFO)
            xbmcgui.Window(target).setProperty('Series.Command', 'select')
            return

    if window_id in (11127, 11129) and xbmcgui.getCurrentWindowDialogId() in (0, 9999):
        selected = focus_id == 30
        if selected and xbmcgui.Window(10000).getProperty("AsterSearch.Ready") == "true":
            xbmc.executebuiltin("SetProperty(AsterSearch.Command,details,home)")
            return
    if (window_id, focus_id) in ((10025, 50), (10000, 100), (10000, 110), (11112, 100), (11112, 110)):
        container = focus_id
        movie_id = xbmc.getInfoLabel(f'Container({container}).ListItem.DBID')
        if (movie_id.isdecimal() and 0 < int(movie_id) <= 2147483647
                and xbmc.getInfoLabel(f'Container({container}).ListItem.DBTYPE') == 'movie'
                and not xbmc.getCondVisibility(f'Container({container}).ListItem.IsParentFolder')):
            xbmc.executebuiltin('RunScript(script.asterruntime,aster-global-search-ui22,movie,' + movie_id + ')')
            return
    if (window_id, focus_id) in ((10025, 50), (10000, 110), (11112, 110)):
        try:
            from aster_v2_series import launch_selected_show
        except ImportError:
            pass
        else:
            if launch_selected_show():return
    if window_id == 10502 and focus_id == 50:
        from books_player import is_books_parent
        if is_books_parent(xbmc.getInfoLabel('Container.FolderPath'),
                           xbmc.getInfoLabel('Container(50).ListItem.Label')):
            xbmc.executebuiltin('ActivateWindow(11110)')
            return
    xbmc.log('AsterSelect: fallback Action(Select)', xbmc.LOGINFO)
    xbmc.executebuiltin('Action(Select)')


if __name__ == '__main__':
    main()
