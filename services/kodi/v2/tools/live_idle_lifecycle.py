"""HP-only temporary saver trial, journalled restore, no playback or AV writes."""
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui
sys.path.insert(0, '/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
ROOT = Path('/storage/.aster-staging/aster-idle-presentation2')
PENDING = Path('/storage/.aster-checkpoints/aster-idle-presentation2/trial-restore-pending.json')
IDENTITY = 'screensaver.asterhome.v2lab'
DIM = 'screensaver.xbmc.builtin.dim'
KEYS = ('screensaver.mode', 'screensaver.time', 'screensaver.usedimonpause',
        'powermanagement.displaysoff', 'powermanagement.shutdowntime', 'powermanagement.shutdownstate')

def require(ok, code):
    if not ok: raise RuntimeError(code)
def until(check, code, seconds=12):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(100)
    raise RuntimeError(code)
def rpc(method, params):
    require(method in ('Settings.GetSettingValue', 'Settings.SetSettingValue', 'Input.ExecuteAction', 'Input.Home'), 'idle-trial-rpc-boundary')
    if method == 'Settings.GetSettingValue': require(params.get('setting') in KEYS, 'idle-trial-read-boundary')
    if method == 'Settings.SetSettingValue':
        require(params.get('setting') == 'screensaver.mode' and params.get('value') in (DIM, IDENTITY), 'idle-trial-write-boundary')
    if method == 'Input.ExecuteAction': require(params.get('action') in ('right', 'select', 'noop'), 'idle-trial-input-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params))))
    require('error' not in reply, 'idle-trial-rpc')
    return reply.get('result')
def current_mode(): return rpc('Settings.GetSettingValue', dict(setting='screensaver.mode'))['value']
def settings(): return {k: rpc('Settings.GetSettingValue', dict(setting=k))['value'] for k in KEYS}
def active(): return xbmc.getCondVisibility('System.ScreenSaverActive')
def menu(): return xbmcgui.Window(10000).getProperty('AsterNetwork.MenuOpen')
def own_window(): return xbmcgui.Window(10000).getProperty('AsterIdle.Window')
def source_focus(): return xbmcgui.getCurrentWindowId() == 10004 and xbmc.getCondVisibility('Control.HasFocus(206)') and not menu()
def write(path, value):
    from tempfile import mkstemp
    fd, temporary = mkstemp(prefix='.idle-proof-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o600); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def main():
    require(os.uname().nodename == 'AsterTV' and sys.argv[1:] in ([], ['--automatic']), 'idle-trial-hp-only')
    automatic = sys.argv[1:] == ['--automatic']
    lock = os.open(str(ROOT/'lifecycle.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cp = None; addon = None; original_choice = None; owned_choice = None; baseline = None
    timer_window = None; timer_original = None; timer_owned = False
    result = dict(passed=False, production_changed=False, automatic_entry_tested=False, checks_enforced=True)
    try:
        require(not PENDING.exists(), 'idle-trial-restore-required')
        require(guard.idle() and xbmcgui.getCurrentWindowId() == 10000 and not active() and not menu() and not own_window(), 'idle-trial-idle-home')
        baseline = settings(); av = guard.snapshot()
        require(baseline['screensaver.mode'] == DIM, 'idle-trial-original-dim')
        # Check the exact installed pilot before selecting it; no add-on update.
        sys.path.insert(0, str(ROOT))
        from idle_screensaver_install import verify_files
        verify_files(ROOT, Path('/storage'), 'f6af15135f9321eb7fc602696051a22b4a07ff8a2b057fd2eef359e1c420dc83')
        addon = xbmcaddon.Addon(IDENTITY); original_choice = addon.getSettingString('presentation')
        require(original_choice in ('', 'black', 'aster'), 'idle-trial-choice-drift')
        cp = Path('/storage/.aster-checkpoints')/('aster-idle-lifecycle-'+str(time.time_ns())); cp.mkdir(mode=0o700)
        timer_window = xbmcgui.Window(11112)
        timer_original = timer_window.getProperty('AsterHub.HomeTimerActive')
        require(timer_original != 'true' and timer_window.getProperty('AsterHub.HomeTimerExpired') != 'true', 'idle-trial-existing-timer')
        journal = dict(settings=baseline, presentation=original_choice, timer_active=timer_original, checkpoint=str(cp), state='restore-required')
        write(cp/'baseline.json', journal); write(PENDING, journal)
        require(rpc('Settings.SetSettingValue', dict(setting='screensaver.mode', value=IDENTITY)) is True, 'idle-trial-select')
        require(current_mode() == IDENTITY, 'idle-trial-not-selected')
        xbmc.executebuiltin('ActivateWindow(Settings)')
        until(lambda: xbmcgui.getCurrentWindowId() == 10004, 'idle-trial-settings-window')
        xbmc.executebuiltin('Control.SetFocus(206)'); until(source_focus, 'idle-trial-source-focus')
        xbmc.sleep(1300)
        xbmc.executebuiltin('TakeScreenshot('+str(cp/'before-settings.png')+')'); xbmc.sleep(650)
        cycles = []
        for presentation in ('black', 'aster'):
            addon.setSettingString('presentation', presentation); owned_choice = presentation
            require(addon.getSettingString('presentation') == presentation, 'idle-trial-choice-write')
            for repeat in range(2):
                for action in ('right', 'select'):
                    require(source_focus() and guard.idle() and not own_window(), 'idle-trial-cycle-context')
                    require(current_mode() == IDENTITY and addon.getSettingString('presentation') == owned_choice, 'idle-trial-setting-race')
                    result['phase'] = dict(presentation=presentation, repeat=repeat+1, input=action)
                    until(lambda: xbmcgui.getCurrentWindowDialogId() in (-1, 0, 9999), 'idle-trial-foreign-dialog')
                    rpc('Input.ExecuteAction', dict(action='noop')); xbmc.sleep(350)
                    xbmc.executebuiltin('ActivateScreensaver')
                    until(lambda: active() and bool(own_window()), 'idle-trial-no-custom-window')
                    xbmc.sleep(2600)
                    require(active() and bool(own_window()) and guard.idle(), 'idle-trial-early-exit')
                    if repeat == 0 and action == 'right':
                        xbmc.executebuiltin('TakeScreenshot('+str(cp/(presentation+'.png'))+')'); xbmc.sleep(500)
                    rpc('Input.ExecuteAction', dict(action=action))
                    until(lambda: not active() and not own_window(), 'idle-trial-wake-cleanup')
                    # Kodi Omega's native Dim layer has a1s close animation.
                    # Do not start another saver or change its mode mid-close.
                    xbmc.sleep(1300)
                    require(source_focus() and guard.idle(), 'idle-trial-wake-reached-page')
                    cycles.append(dict(presentation=presentation, input=action, repeat=repeat+1, consumed=True, focus_preserved=True))
        result.update(cycles=cycles, rendered_both=True)
        # The approved synthetic property exercises attention handling without
        # creating a real timer or altering Home's timer/alarm implementation.
        class Events(xbmc.Monitor):
            activations = 0
            def onScreensaverActivated(self): self.activations += 1
        events = Events()
        timer_window.setProperty('AsterHub.HomeTimerActive', 'true'); timer_owned = True
        previous_events = events.activations
        rpc('Input.ExecuteAction', dict(action='noop')); xbmc.sleep(350)
        xbmc.executebuiltin('ActivateScreensaver')
        until(lambda: events.activations > previous_events, 'idle-trial-timer-no-activation')
        until(lambda: not active() and not own_window(), 'idle-trial-timer-not-protected')
        xbmc.sleep(1300)
        require(source_focus() and guard.idle(), 'idle-trial-timer-source-drift')
        if timer_original: timer_window.setProperty('AsterHub.HomeTimerActive', timer_original)
        else: timer_window.clearProperty('AsterHub.HomeTimerActive')
        timer_owned = False
        result['synthetic_timer_attention_passed'] = True
        if automatic:
            require(baseline['screensaver.time'] == 3, 'idle-trial-three-minute-baseline')
            addon.setSettingString('presentation', 'black'); owned_choice = 'black'
            rpc('Input.ExecuteAction', dict(action='noop'))
            started = time.monotonic(); deadline = started + 205
            while not (active() and own_window()) and time.monotonic() < deadline:
                require(guard.idle() and current_mode() == IDENTITY, 'idle-trial-auto-context')
                xbmc.sleep(500)
            require(active() and bool(own_window()), 'idle-trial-automatic-not-entered')
            elapsed = time.monotonic() - started
            require(170 <= elapsed <= 205, 'idle-trial-automatic-early-entry')
            rpc('Input.ExecuteAction', dict(action='select'))
            until(lambda: not active() and not own_window(), 'idle-trial-automatic-wake')
            xbmc.sleep(1300)
            require(source_focus() and guard.idle(), 'idle-trial-automatic-focus')
            result.update(automatic_entry_tested=True, automatic_seconds=round(elapsed, 1),
                          automatic_wake_consumed=True)
    except Exception as error:
        code = str(error); result.update(passed=False, code=code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__)
        result['failure_state'] = dict(active=active(), custom_window=bool(own_window()),
                                       dialog=xbmcgui.getCurrentWindowDialogId(), window=xbmcgui.getCurrentWindowId(),
                                       timer_active=xbmc.getInfoLabel('Window(11112).Property(AsterHub.HomeTimerActive)') == 'true',
                                       timer_expired=xbmc.getInfoLabel('Window(11112).Property(AsterHub.HomeTimerExpired)') == 'true')
    finally:
        if cp is not None:
            try:
                require(guard.idle(), 'idle-trial-foreign-player')
                if timer_owned:
                    require(timer_window.getProperty('AsterHub.HomeTimerActive') == 'true', 'idle-trial-foreign-timer')
                    if timer_original: timer_window.setProperty('AsterHub.HomeTimerActive', timer_original)
                    else: timer_window.clearProperty('AsterHub.HomeTimerActive')
                    timer_owned = False
                if active():
                    rpc('Input.ExecuteAction', dict(action='noop'))
                    until(lambda: not active() and not own_window(), 'idle-trial-final-wake')
                    xbmc.sleep(1300)
                require(current_mode() in (IDENTITY, DIM), 'idle-trial-foreign-mode')
                require(addon.getSettingString('presentation') in (owned_choice, original_choice), 'idle-trial-foreign-choice')
                if current_mode() == IDENTITY:
                    require(rpc('Settings.SetSettingValue', dict(setting='screensaver.mode', value=DIM)) is True, 'idle-trial-restore-mode')
                addon.setSettingString('presentation', original_choice)
                require(settings() == baseline and addon.getSettingString('presentation') == original_choice, 'idle-trial-restore-check')
                require(guard.snapshot() == av, 'idle-trial-av-drift')
                if source_focus():
                    xbmc.sleep(1300)
                    xbmc.executebuiltin('TakeScreenshot('+str(cp/'after-settings.png')+')'); xbmc.sleep(650)
                if xbmcgui.getCurrentWindowId() == 10004 and not menu(): rpc('Input.Home', {})
                until(lambda: xbmcgui.getCurrentWindowId() == 10000, 'idle-trial-home-return')
                require(not active() and not own_window() and guard.idle(), 'idle-trial-final-state')
                PENDING.unlink(); result.update(passed='code' not in result, original_settings_restored=True,
                                               av_settings_unchanged=True, idle_empty=True)
            except Exception as error:
                result.update(passed=False, restoration_required=True, restore_code=type(error).__name__)
            write(cp/'native.json', result)
        os.close(lock)

if __name__ == '__main__': main()
