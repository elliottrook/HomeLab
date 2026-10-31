#!/usr/bin/env python3
"""Apply the bounded AsterTV v2 lab acceptance repairs with hash guards.

The r9 preservation archive remains the base.  This overlay changes only
reviewed text members, checkpoints every original, refuses active playback,
and verifies every replacement before Kodi is restarted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile


LAB_HOST = "AsterTV"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-acceptance-r10-20261030")


def active_window_helper(name: str) -> str:
    return (
        f"\n\ndef {name}(window_id):\n"
        "    return (xbmcgui.getCurrentWindowId() == window_id or\n"
        "            xbmc.getCondVisibility('Window.IsActive(' + str(window_id) + ')'))\n"
    )


REPAIRS = {
    "skin.asterhome/1080i/custom_1113_music.xml": {
        "before": "1b08d8b728333e80a92fa40b1423a95213970de8bd3db74b792a352c0fae4a16",
        "replace": [
            ('<param name="gridup" value="116" /><param name="topdown" value="116" />',
             '<param name="gridup" value="110" /><param name="topdown" value="110" />'),
        ],
    },
    "skin.asterhome/tools/youtube_back.py": {
        "before": "3b01bfc1771d3aa53d7eb121295497dad9e0b539620889052d5f62b0fb8ff8cf",
        "replace": [
            ("AlarmClock(AsterYouTubeBackFocus,SetFocus(9530),00:01,silent)",
             "AlarmClock(AsterYouTubeBackFocus,SetFocus(9300),00:01,silent)"),
        ],
    },
    "skin.asterhome/tools/youtube_root_focus.py": {
        "before": "2fe1fdd463d021fed82f2f19a614d419e171884e2b229c2d23e23e6eb60f436c",
        "replace": [
            ("""        if focused in ROOT_CONTROLS:
            return  # The owner is already on a visible root control.
        if focused:
            xbmc.executebuiltin(f"SetFocus({SEARCH_BUTTON})")
            return
        xbmc.sleep(100)
""",
             """        if focused in ROOT_CONTROLS:
            return  # The owner is already on a visible root control.
        # Kodi 22 can leave this custom root with focus 0 after an async
        # Container.Update.  The root pills already exist, so retry the owned
        # Search pill until Kodi acknowledges it instead of waiting for a
        # non-zero focus that may never arrive.
        xbmc.executebuiltin(f"SetFocus({SEARCH_BUTTON})")
        xbmc.sleep(100)
"""),
        ],
    },
    "screensaver.asterhome.v2lab/resources/skins/Default/1080i/AsterIdle.xml": {
        "before": "9f61e6a1788448b4dba2eb09b5ee295cab85b5d36ddbe8e531cfbb2a8d3245aa",
        "replace": [
            ("<backgroundcolor>00000000</backgroundcolor>",
             "<backgroundcolor>ff000000</backgroundcolor>"),
            ("""    <controls>
        <control type="image" id="10">
""",
             """    <controls>
        <control type="image" id="9">
            <left>0</left><top>0</top><width>1920</width><height>1080</height>
            <texture>special://home/addons/screensaver.asterhome.v2lab/resources/solid.png</texture>
            <colordiffuse>ff000000</colordiffuse><aspectratio>stretch</aspectratio>
        </control>
        <control type="image" id="10">
"""),
        ],
    },
    "script.asterseerr/default.py": {
        "before": "0fb1695faee3f1a21dbdbd8d65b4a98a7ccb5d14b8d0b6d36e5983ed6bb1b36c",
        "replace": [
            ("PREFIX = 'AsterSeerr.'\n", "PREFIX = 'AsterSeerr.'" + active_window_helper("window_active") + "\n"),
            ("while xbmcgui.getCurrentWindowId() != 11132:", "while not window_active(11132):"),
            ("while xbmcgui.getCurrentWindowId() == 11132 and not monitor.abortRequested():",
             "while window_active(11132) and not monitor.abortRequested():"),
            ("if opened and xbmcgui.getCurrentWindowId() == 11132:",
             "if opened and window_active(11132):"),
        ],
    },
    "script.astervoice.v2lab/default.py": {
        "before": "66b9d1339a028d6bf0c515b874ed001b605626c49fab0b607f5834f4a497912a",
        "replace": [
            ("SEARCH_WINDOW = 11127\n", "SEARCH_WINDOW = 11127" + active_window_helper("window_active") + "\n"),
            ("require(xbmcgui.getCurrentWindowId() in (10000, SEARCH_WINDOW),\n                'voice-foreground-context')",
             "require(window_active(10000) or window_active(SEARCH_WINDOW),\n                'voice-foreground-context')"),
            ("if xbmcgui.getCurrentWindowId() != SEARCH_WINDOW:", "if not window_active(SEARCH_WINDOW):"),
            ("while not (xbmcgui.getCurrentWindowId() == SEARCH_WINDOW\n                       and home.getProperty(PREFIX + 'Ready') == 'true'):",
             "while not (window_active(SEARCH_WINDOW)\n                       and home.getProperty(PREFIX + 'Ready') == 'true'):"),
            ("or xbmcgui.getCurrentWindowId() != SEARCH_WINDOW", "or not window_active(SEARCH_WINDOW)"),
            ("if xbmcgui.getCurrentWindowId() == SEARCH_WINDOW:", "if window_active(SEARCH_WINDOW):"),
        ],
    },
    "script.asterruntime/aster-camera2/view.py": {
        "before": "71d9788eb8c686218fa8927d66b8188f290ba0efe6962d635b99610a4568dcb5",
        "replace": [
            ("import sys\nimport time\n", "import sys\nimport time\nimport subprocess\n"),
            ("BASE='http://127.0.0.1:15102'\n", "BASE='http://127.0.0.1:15102'" + active_window_helper("window_active") + "\n"),
            ("""def stopped(window,message='Ready · images on request'):
""",
             """def camera_service(action):
    if action not in ('start','stop'):raise ValueError('camera-service-action')
    subprocess.run(['/usr/bin/systemctl',action,'aster-camera.service'],
                   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL,timeout=8,check=True)

def stopped(window,message='Ready · images on request'):
"""),
            ("""    if action=='leave':
        try:request('/view/stop',True)
        except Exception:pass
        stopped(xbmcgui.Window(11112));status_page('leave');return
    if xbmcgui.getCurrentWindowId()!=11112:
""",
             """    if action=='leave':
        try:request('/view/stop',True)
        except Exception:pass
        try:camera_service('stop')
        except Exception:pass
        stopped(xbmcgui.Window(11112));status_page('leave');return
    if not window_active(11112):
"""),
            ("""    if action=='entry':status_page('entry')
    window=xbmcgui.Window(11112);window.setProperty('AsterHub.HomeCameraLabel','Front of house')
    try:
        state=request('/status')
        if action=='entry':
            if state['active']:request('/view/stop',True)
            stopped(window);return
        if action=='toggle':
""",
             """    if action=='entry':
        status_page('entry')
        stopped(xbmcgui.Window(11112));return
    window=xbmcgui.Window(11112);window.setProperty('AsterHub.HomeCameraLabel','Front of house')
    try:
        if action=='toggle':
            camera_service('start')
            deadline=time.monotonic()+6
            while True:
                try:state=request('/status');break
                except Exception:
                    if time.monotonic()>=deadline:raise
                    xbmc.sleep(100)
        else:state=request('/status')
        if action=='toggle':
"""),
            ("""            if state['active']:
                request('/view/stop',True);stopped(window);return
""",
             """            if state['active']:
                request('/view/stop',True);camera_service('stop');stopped(window);return
"""),
            ("""            if not state['active']:
                stopped(window,'Unavailable · select Live view to retry' if state.get('failures') else 'Ready · five-minute view ended');return
""",
             """            if not state['active']:
                camera_service('stop')
                stopped(window,'Unavailable · select Live view to retry' if state.get('failures') else 'Ready · five-minute view ended');return
"""),
            ("""    except Exception:
        stopped(window,'Camera viewer unavailable')
""",
             """    except Exception:
        try:camera_service('stop')
        except Exception:pass
        stopped(window,'Camera viewer unavailable')
"""),
        ],
    },
    "skin.asterhome/1080i/custom_1112_home.xml": {
        "before": "1906c5bfcd8718b702c7c3881da4bdc7a68a2840a025972e32cfde1272840606",
        "replace": [
            ("<onclick>Control.SetFocus(302)</onclick><onleft>307</onleft>",
             "<onclick>RunScript(script.asterruntime,aster-camera2,view,toggle)</onclick><onclick>Control.SetFocus(302)</onclick><onleft>307</onleft>"),
        ],
    },
    "skin.asterhome/1080i/custom_1111_digest.xml": {
        "before": "55954356204a133fd23b504d5b0162a3b020a59080653778287e7543bfc9af73",
        "replace": [
            ("""        <onright>301</onright>
        <itemlayout height="62" width="850">
""",
             """        <onright>301</onright>
        <onclick>RunScript(special://skin/tools/hub_data.py,digest,chapter)</onclick>
        <itemlayout height="62" width="850">
"""),
        ],
    },
    "skin.asterhome/tools/aster_v2_digest.py": {
        "before": "219a9ee7f0c570f8853eb86d9be58512844df69013141c546f7edaef2db7c3ca",
        "replace": [
            ("""        if not idle() or xbmcgui.getCurrentWindowId() != 11111: raise ValueError('idle-news-required')
""",
             """        news_active = lambda: (xbmcgui.getCurrentWindowId() == 11111 or xbmc.getCondVisibility('Window.IsActive(1111)'))
        if not idle() or not news_active(): raise ValueError('idle-news-required')
"""),
            ("or xbmcgui.getCurrentWindowId() != 11111 or window.getFocusId() != focus):",
             "or not news_active() or window.getFocusId() != focus):"),
        ],
    },
    "script.asterruntime/aster-digest-player8/default.py": {
        "before": "25d6180334e14d885fa047d2485e10b7b920576323a0e772e314f2724a27c4c2",
        "replace": [
            ("        self.publish(0)\n", "        self.publish(0)\n        self.ui_ready = True\n"),
            ("""def until(check, code, seconds=10):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(50)
    raise ValueError(code)
""",
             """def until(check, code, seconds=10):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(50)
    raise ValueError(code)

def window_active(window_id):
    return (xbmcgui.getCurrentWindowId() == window_id or
            xbmc.getCondVisibility('Window.IsActive(' + str(window_id) + ')'))

def source_window_id():
    return 11111 if window_active(11111) else xbmcgui.getCurrentWindowId()
"""),
            ("source_window = xbmcgui.getCurrentWindowId()", "source_window = source_window_id()"),
            ("require(idle() and xbmcgui.getCurrentWindowId() == source_window\n            and xbmcgui.Window(source_window).getFocusId() == source_focus, 'source-changed')",
             "require(idle() and window_active(source_window)\n            and xbmcgui.Window(source_window).getFocusId() == source_focus, 'source-changed')"),
            ("until(lambda:xbmcgui.getCurrentWindowId() in (source_window, 10000), 'source-not-restored', 4)\n                    if xbmcgui.getCurrentWindowId() == source_window:",
             "until(lambda:window_active(source_window) or window_active(10000), 'source-not-restored', 4)\n                    if window_active(source_window):"),
            ("""        window.show()
        until(lambda:window.identity is not None, 'player-ui-not-ready', 4)
""",
             """        window.adapter = None
        window.port = None
        window.finished = False
        window.ui_ready = False
        window.show()
        # onInit can still see the source custom window on Kodi 22.  Resolve
        # the allocated WindowXML identity only after the visible window has
        # actually changed, as the stable Series page already does.
        until(lambda: window.ui_ready and xbmcgui.getCurrentWindowId() not in (0, 10000, source_window),
              'player-ui-not-ready', 4)
        window.identity = xbmcgui.getCurrentWindowId()
        xbmcgui.Window(10000).setProperty('AsterDigest.PlayerWindow', str(window.identity))
"""),
        ],
    },
    "script.asterruntime/aster-digest-reader6/default.py": {
        "before": "b06d8305dd0658f245a0f9ea54fa0202cedf139277d34f39fd71ae0e4e0c002a",
        "replace": [
            ("""def context(args, window, focus, ready):
""",
             """def window_active(window_id):
    return (xbmcgui.getCurrentWindowId() == window_id or
            xbmc.getCondVisibility('Window.IsActive(' + str(window_id) + ')'))

def source_window_id():
    return 11111 if window_active(11111) else xbmcgui.getCurrentWindowId()

def focused_control(window, window_id):
    try:
        reported = window.getFocusId()
    except RuntimeError:
        reported = 0
    if reported:
        return reported
    if window_id == 11111:
        for control_id in (312, 310, 311, 301, 305, 300, 302, 304, 303, 500):
            if xbmc.getCondVisibility('Control.HasFocus(' + str(control_id) + ')'):
                return control_id
    return reported

def context(args, window, focus, ready):
"""),
            ("source_id = xbmcgui.getCurrentWindowId()", "source_id = source_window_id()"),
            ("source_focus = source.getFocusId()", "source_focus = focused_control(source, source_id)"),
            ("if not idle() or xbmcgui.getCurrentWindowId() != source_id or source.getFocusId() != source_focus: return",
             "if not idle() or not window_active(source_id) or focused_control(source, source_id) != source_focus: return"),
            ("if (xbmcgui.getCurrentWindowId() == 11111 and\n                            source.getProperty('AsterHub.Ready') == 'true'",
             "if (window_active(11111) and\n                            source.getProperty('AsterHub.Ready') == 'true'"),
            ("if xbmcgui.getCurrentWindowId() in (source_id, 10000): break",
             "if window_active(source_id) or window_active(10000): break"),
            ("if idle() and xbmcgui.getCurrentWindowId() == source_id and source_focus:",
             "if idle() and window_active(source_id) and source_focus:"),
            ("""        window.show()
        monitor = xbmc.Monitor()
        try:
            for _ in range(80):
                if window.identity is not None: break
                if monitor.waitForAbort(.05): return
""",
             """        window.show()
        # WindowXML.onInit may report the source page before Kodi publishes
        # the allocated reader ID.  Discard that provisional identity and
        # wait for the actual visible WindowXML.
        window.identity = None
        monitor = xbmc.Monitor()
        try:
            for _ in range(80):
                current = xbmcgui.getCurrentWindowId()
                if current not in (0, 10000, source_id):
                    window.identity = current
                    home.setProperty('AsterDigest.ReaderWindow', str(current))
                    break
                if monitor.waitForAbort(.05): return
"""),
        ],
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patched(relative: str, data: bytes) -> bytes:
    spec = REPAIRS[relative]
    if sha(data) != spec["before"]:
        raise RuntimeError("unexpected live hash: " + relative)
    text = data.decode("utf-8")
    for old, new in spec["replace"]:
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f"replacement count {count}: {relative}")
        text = text.replace(old, new, 1)
    result = text.encode("utf-8")
    if result == data:
        raise RuntimeError("empty repair: " + relative)
    return result


def live_path(relative: str, storage: Path) -> Path:
    if relative.startswith("skin.asterhome/"):
        return storage / ".kodi/addons" / relative
    if relative.startswith("script.") or relative.startswith("screensaver."):
        return storage / ".kodi/addons" / relative
    raise RuntimeError("unsupported repair target: " + relative)


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r10-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate(storage: Path) -> dict[str, str]:
    result = {}
    for relative in REPAIRS:
        current = live_path(relative, storage).read_bytes()
        result[relative] = sha(patched(relative, current))
    return result


def install(storage: Path) -> None:
    if os.uname().nodename != LAB_HOST or storage != Path("/storage"):
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists():
        raise RuntimeError("checkpoint already exists")
    if Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("recovery marker present")
    candidates = {relative: patched(relative, live_path(relative, storage).read_bytes())
                  for relative in REPAIRS}
    active_players()
    CHECKPOINT.mkdir(mode=0o700)
    evidence = {"kind": "astertv-v2-acceptance-r10", "files": {}}
    for relative, candidate in candidates.items():
        source = live_path(relative, storage)
        original = source.read_bytes()
        checkpoint = CHECKPOINT / relative.replace("/", "__")
        checkpoint.write_bytes(original)
        checkpoint.chmod(0o600)
        evidence["files"][relative] = {"before": sha(original), "after": sha(candidate)}
    (CHECKPOINT / "manifest.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (CHECKPOINT / "manifest.json").chmod(0o600)
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for relative, candidate in candidates.items():
            target = live_path(relative, storage)
            if sha(target.read_bytes()) != REPAIRS[relative]["before"]:
                raise RuntimeError("live drift while Kodi stopped: " + relative)
            atomic_write(target, candidate)
        for relative, candidate in candidates.items():
            if sha(live_path(relative, storage).read_bytes()) != sha(candidate):
                raise RuntimeError("installed hash mismatch: " + relative)
    except Exception:
        for relative in candidates:
            target = live_path(relative, storage)
            original = (CHECKPOINT / relative.replace("/", "__")).read_bytes()
            atomic_write(target, original)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "files": evidence["files"]}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage", type=Path, default=Path("/storage"))
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate(args.storage), indent=2, sort_keys=True))
    else:
        install(args.storage)


if __name__ == "__main__":
    main()
