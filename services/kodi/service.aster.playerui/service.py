"""Local Pause-to-OSD, with single-edge activation and interaction-safe hiding."""
import time


class PauseOSD:
    def __init__(self):
        self.paused = False
        self.managed = False
        self.hide_at = None

    def step(self, *, video, paused, fullscreen, osd, blocked, idle, now, aster=True):
        if not video or not fullscreen or not aster:
            self.paused = paused
            self.managed = False
            self.hide_at = None
            return None
        rising = paused and not self.paused
        self.paused = paused
        if rising:
            self.hide_at = None
            self.managed = not blocked
            return 'open' if self.managed and not osd else None
        if self.managed and not osd:
            # Explicit Back/OSD dismissal wins: never reopen while still paused.
            self.managed = False
            self.hide_at = None
        if paused:
            self.hide_at = None
        elif self.managed and osd:
            if blocked or not idle:
                self.hide_at = now + 3
            elif self.hide_at is None:
                self.hide_at = now + 3
            elif now >= self.hide_at:
                self.managed = False
                self.hide_at = None
                return 'close'
        return None


def run():
    import os
    import xbmc
    import xbmcgui
    if os.uname().nodename != 'AsterTV':
        return  # HP pilot only, even if accidentally copied to production.
    home = xbmcgui.Window(10000)
    if home.getProperty('AsterPlayerUI.Running'):
        return
    home.setProperty('AsterPlayerUI.Running', 'true')
    monitor = xbmc.Monitor()
    controller = PauseOSD()
    visible = xbmc.getCondVisibility
    counts = dict(opened=0, closed=0)
    try:
        while not monitor.waitForAbort(.1):
            state = dict(video=visible('Player.HasVideo'), paused=visible('Player.Paused'),
                         fullscreen=visible('Window.IsActive(fullscreenvideo)'),
                         osd=visible('Window.IsVisible(videoosd)'),
                         blocked=xbmcgui.getCurrentWindowDialogId() not in (0, 9999, 12901),
                         idle=visible('System.IdleTime(3)'), now=time.monotonic(),
                         aster=xbmc.getSkinDir() == 'skin.asterhome')
            action = controller.step(**state)
            if action == 'open':
                # Native dialog activation, not OSD toggle (which could close it).
                xbmc.executebuiltin('ActivateWindow(videoosd)')
                counts['opened'] += 1
            elif action == 'close':
                xbmc.executebuiltin('Dialog.Close(videoosd)')
                counts['closed'] += 1
            if action:
                for name, count in counts.items():
                    home.setProperty('AsterPlayerUI.' + name, str(count))
    finally:
        home.clearProperty('AsterPlayerUI.Running')


if __name__ == '__main__': run()
