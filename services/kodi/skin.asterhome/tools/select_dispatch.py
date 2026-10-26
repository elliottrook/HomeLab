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


def series_command_target(identity, visible, focus_id):
    """Return the verified scripted-window identity for an OK command."""
    if (not isinstance(identity, str) or not identity.isdecimal()
            or not visible or focus_id not in SERIES_CONTROLS):
        return None
    value = int(identity)
    return value if 12000 <= value <= 13999 else None


def dispatched_action(window_id, focus_id):
    """Return a trusted built-in for an Aster dynamic list, or ``None``."""
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
    return None


def main():
    import xbmc
    import xbmcgui

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
            xbmcgui.Window(target).setProperty('Series.Command', 'select')
            return

    window_id = xbmcgui.getCurrentWindowId()
    try:
        focus_id = xbmcgui.Window(window_id).getFocusId()
    except RuntimeError:
        focus_id = 0
    if window_id == 10502 and focus_id == 50:
        from books_player import is_books_parent
        if is_books_parent(xbmc.getInfoLabel('Container.FolderPath'),
                           xbmc.getInfoLabel('Container(50).ListItem.Label')):
            xbmc.executebuiltin('ActivateWindow(11110)')
            return
    xbmc.executebuiltin(dispatched_action(window_id, focus_id) or 'Action(Select)')


if __name__ == '__main__':
    main()
