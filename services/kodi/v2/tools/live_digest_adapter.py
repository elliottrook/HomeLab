"""HP-only bounded current cached briefing adapter trial; no normal entry."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request
import uuid
import xbmc
import xbmcgui
import xbmcvfs

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from digest_timeline import build
from digest_kodi_port import KodiPort, idle
from digest_player_adapter import Adapter
import deploy_startup as guard


def require(value, code):
    if not value: raise RuntimeError(code)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): raise ValueError('redirect-refused')


def feed_bytes():
    with urllib.request.build_opener(NoRedirect()).open('http://192.168.70.13:8080/static/digest-audio/latest.json', timeout=8) as response:
        raw = response.read(262145)
    require(len(raw) <= 262144, 'bounded-feed-required')
    return raw


def until(check, code, seconds=10):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(50)
    raise RuntimeError(code)


port = None
checkpoint = None
source_focus = None
result = dict(passed=False, native_adapter=True, normal_news_changed=False,
    production_changed=False, source_writes=False, narration_generated=False, checks_enforced=True)
try:
    require(os.uname().nodename == 'AsterTV' and idle() and xbmcgui.getCurrentWindowId() == 10000, 'hp-home-idle-required')
    source_focus = xbmcgui.Window(10000).getFocusId()
    manifest_bytes = (ROOT / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    require(manifest['kind'] == 'hp-digest-adapter-trial.v1' and len(manifest['files']) == 6, 'bounded-stage-required')
    for row in manifest['files']:
        require(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], 'stage-member-drift')
    before = guard.snapshot()
    checkpoint = Path('/storage/.aster-checkpoints') / ('aster-digest-adapter-' + str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    (checkpoint / 'manifest.json').write_bytes(manifest_bytes)
    (checkpoint / 'before.json').write_text(json.dumps(before))
    raw = feed_bytes()
    feed = json.loads(raw)
    provisional = build(feed, feed['duration_seconds'], datetime.now(timezone.utc))
    source = Path(xbmcvfs.translatePath('special://temp/skin.asterhome/digest')) / (
        'digest-' + hashlib.sha256(feed['generated_at'].encode()).hexdigest()[:16] + '.mp3')
    require(source.is_file() and not source.is_symlink() and 0 < source.stat().st_size <= 32*1024*1024, 'existing-bounded-cache-required')
    media = source.read_bytes()
    digest = hashlib.sha256(media).hexdigest()
    target = checkpoint / ('session-' + uuid.uuid4().hex + '.mp3')
    with target.open('xb') as handle:
        os.chmod(target, 0o600)
        handle.write(media)
    require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, 'private-copy-not-verified')
    require(feed_bytes() == raw and idle() and xbmcgui.getCurrentWindowId() == 10000
        and xbmcgui.Window(10000).getFocusId() == source_focus, 'source-changed-before-open')
    port = KodiPort(target, digest, provisional.identity)
    port.open()
    until(lambda:port.owned() and port.duration() > 0 and 0 <= port.player.getTime() < 5, 'owned-opening-not-observed')
    timeline = build(feed, port.duration(), datetime.now(timezone.utc))
    require(feed_bytes() == raw, 'edition-changed-during-open')
    port.edition = timeline.identity
    adapter = Adapter(timeline, port.session, port.media, port)
    initial = adapter.poll()
    require(initial.phase in ('opening', 'story') and initial.elapsed < 5, 'opening-not-preserved')
    checks = []
    for index in sorted(set((min(1, len(timeline.chapters)-1), len(timeline.chapters)-1))):
        adapter.seek(index)
        view = adapter.poll()
        result['last_seek'] = dict(expected_chapter=index, observed_chapter=view.chapter,
            offset_from_marker=round(view.elapsed-timeline.chapters[index].start, 3), fenced=adapter.fenced,
            readback_pending=adapter.pending is not None)
        require(not adapter.fenced and adapter.pending is None and view.chapter == index, 'seek-highlight-readback')
        checks.append(index)
    require(adapter.close() and idle(), 'owned-exit-stop-not-confirmed')
    require(guard.snapshot() == before, 'settings-navigation-preservation')
    result.update(passed=True, observed_duration_verified=True, opening_preserved=True,
        marker_readbacks=len(checks), highlight_from_audio=True, owned_exit_stop=True,
        settings_navigation_unchanged=True, session_copy_verified=True)
except Exception as error:
    message = str(error)
    result['code'] = message if re.fullmatch('[a-z0-9-]{1,100}', message) else type(error).__name__
finally:
    if port is not None and not port.stopping and port.owned():
        port.stop()
        result['cleanup_stop_confirmed'] = port.idle()
    if port is not None:
        result['av_start_events'] = port.player.starts
    result['idle_empty'] = idle()
    if result['idle_empty'] and source_focus:
        xbmc.executebuiltin('ActivateWindow(Home)')
        until(lambda:xbmcgui.getCurrentWindowId() == 10000, 'home-not-restored')
        xbmc.executebuiltin('Control.SetFocus(' + str(source_focus) + ')')
    if checkpoint is not None:
        (checkpoint / 'native.json').write_text(json.dumps(result, indent=2))
