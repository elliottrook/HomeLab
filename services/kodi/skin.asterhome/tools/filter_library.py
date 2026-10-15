"""Local view filters; never updates Kodi/Jellyfin metadata or playback state."""
import os
import sys
import xml.etree.ElementTree as ET

CATEGORIES = {
    'tv-shows.xsp': ('tvshows', 'TV Shows', 'Shows'),
    'movies.xsp': ('movies', 'Movies', 'Movies'),
    'archive-tv.xsp': ('tvshows', 'Archive TV', 'Archive TV'),
    'archive-film.xsp': ('movies', 'Archive Film', 'Archive Movies'),
}


def build_playlist(filename, genre='', minimum=None):
    kind, name, tag = CATEGORIES[filename]
    root = ET.Element('smartplaylist', type=kind)
    ET.SubElement(root, 'name').text = name
    ET.SubElement(root, 'match').text = 'all'
    for field, operator, value in [('tag', 'is', tag),
                                   ('genre', 'contains', genre),
                                   ('rating', 'greaterthan', str(minimum - 0.001) if minimum is not None else '')]:
        if value:
            rule = ET.SubElement(root, 'rule', field=field, operator=operator)
            ET.SubElement(rule, 'value').text = value
    ET.SubElement(root, 'order', direction='ascending').text = 'title'
    return ET.tostring(root, encoding='unicode')


def main(action):
    import xbmc
    import xbmcgui
    import xbmcvfs
    from urllib.parse import unquote, urlsplit

    path = xbmc.getInfoLabel('Container.FolderPath')
    filename = os.path.basename(unquote(urlsplit(path).path).rstrip('/'))
    if filename not in CATEGORIES:
        xbmcgui.Dialog().notification('Aster Home', 'Open a TV or Film category to filter.')
        return
    genre, minimum = '', None
    # Recover only our own bounded local view state, not arbitrary playlist rules.
    output = 'special://profile/addon_data/skin.asterhome/filters/' + filename
    if path == output or xbmcvfs.translatePath(path) == xbmcvfs.translatePath(output):
        with xbmcvfs.File(output) as source:
            root = ET.fromstring(source.read())
        genre = root.findtext("rule[@field='genre']/value", '')
        threshold = root.findtext("rule[@field='rating']/value")
        if threshold is not None:
            minimum = round(float(threshold) + 0.001, 3)
    if action == 'genre':
        value = xbmcgui.Dialog().input('Genre contains (e.g. Drama)', genre)
        # Cancelling the native keyboard must not clear an existing filter.
        if not value and genre:
            return
        genre = value.strip()[:80]
    elif action == 'rating':
        value = xbmcgui.Dialog().input('Minimum score 0–10', str(minimum) if minimum is not None else '')
        if not value:
            return
        try:
            minimum = float(value)
            if not 0 <= minimum <= 10:
                raise ValueError
        except ValueError:
            xbmcgui.Dialog().notification('Aster Home', 'Enter a score between 0 and 10.')
            return
    elif action == 'clear':
        xbmc.executebuiltin('Container.Update(special://skin/playlists/' + filename + ',replace)')
        return
    else:
        return
    directory = xbmcvfs.translatePath('special://profile/addon_data/skin.asterhome/filters/')
    os.makedirs(directory, exist_ok=True)
    destination = os.path.join(directory, filename)
    # Atomic replacement of this script's generated view file only.
    with open(destination + '.tmp', 'w', encoding='utf-8') as target:
        target.write(build_playlist(filename, genre, minimum))
    os.replace(destination + '.tmp', destination)
    window = xbmcgui.Window(10025)
    window.setProperty('AsterFilterGenre', genre or 'All')
    window.setProperty('AsterFilterScore', str(minimum) + '+' if minimum is not None else 'Any')
    xbmc.executebuiltin('Container.Update(' + output + ',replace)')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
