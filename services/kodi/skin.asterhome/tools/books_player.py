"""Focus the first real chapter after Kodi populates its native music list."""


def is_books_parent(folder, label):
    return (folder.startswith('plugin://plugin.audio.asterbooks/')
            and label == '..')


def focus_first_entry(xbmc, xbmcgui):
    monitor = xbmc.Monitor()
    entered = False
    for _ in range(40):
        if xbmcgui.getCurrentWindowId() != 10502:
            if entered or monitor.waitForAbort(0.1):
                return
            continue
        entered = True
        folder = xbmc.getInfoLabel('Container.FolderPath')
        if folder and not folder.startswith('plugin://plugin.audio.asterbooks/'):
            return
        try:
            window = xbmcgui.Window(10502)
            count = int(xbmc.getInfoLabel('Container(50).NumItems') or 0)
            label = xbmc.getInfoLabel('Container(50).ListItem.Label')
            if count > 0 and label:
                if window.getFocusId() == 50 and is_books_parent(folder, label):
                    xbmc.executebuiltin('SetFocus(50,1,absolute)')
                return
        except (RuntimeError, AttributeError, ValueError):
            pass
        if monitor.waitForAbort(0.1):
            return


if __name__ == '__main__':
    import xbmc
    import xbmcgui
    focus_first_entry(xbmc, xbmcgui)
