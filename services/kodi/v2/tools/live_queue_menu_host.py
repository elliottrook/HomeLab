"""Short-lived HP native ShuffleLab host for five-occurrence Menu testing."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import importlib.util, json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
import xbmc, xbmcgui

_require((os.uname().nodename == 'AsterTV'), ('native-check-failed'))
sys.dont_write_bytecode = True
addon = Path('/storage/.kodi/addons/script.astermusic.v2lab')
spec = importlib.util.spec_from_file_location('aster_queue_menu_test', addon / 'default.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
from music_expanded_trial import ExpandedTrial, save_intent
from music_progressive import ProgressiveSession
from music_trial import save_empty_checkpoint, validate_write
from queue_reader import read_queue

rpc = app.execute
_require((not rpc('Player.GetActivePlayers', {}) and not read_queue(rpc).song_ids), ('native-check-failed'))
view = app.read_catalogue(rpc)
ids = tuple(json.loads(Path('/storage/.aster-checkpoints/aster-music-live-trial-20261023/trial-selection.json').read_text())['song_ids'])
_require((len(ids) == len(set(ids)) == 3 and set(ids) <= set(view.songs)), ('native-check-failed'))
order = (ids[0], ids[1], ids[0], ids[2], ids[1])
root = Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
run = root / ('queue-menu-' + str(time.time_ns()))
run.mkdir(mode=0o700)
expiry = time.monotonic() + 180
grant = run / 'grant.json'
grant.write_text(json.dumps(dict(song_ids=ids, queue_limit=20000, expires_at=int(time.time())+180)))
grant.chmod(0o600)


def transport(method, params):
    if method not in app.READS:
        if method not in ('Player.Stop', 'Playlist.Clear'):
            _require((grant.exists() and time.monotonic() < expiry), ('expired'))
        validate_write(method, params, frozenset(ids), queue_limit=20000)
    return rpc(method, params)


engine = ExpandedTrial(transport, ids, lambda s: save_empty_checkpoint(run/'baseline.json', s),
                       queue_limit=20000, intent=lambda s, **kw: save_intent(run/'intent.json', s, **kw))
session = ProgressiveSession(engine)
window = app.ShuffleLab('AlbumLab.xml', str(addon), 'Default', '1080i')
window.allowed=order; window.queue_limit=20000; window.title='Queue editing lab test'
window.artwork=app.ASSETS+app.ICONS['album']; window.session=session; window.catalogue=view
window.selection=SimpleNamespace(album_id='queue-menu-test', disc_numbers_available=False,
    tracks=tuple(SimpleNamespace(song_id=i, disc=0, track=n+1, title=view.songs[i].get('label','Untitled'), duration=0)
                 for n,i in enumerate(order)))
passed=False
try:
    window.show()
    deadline=time.monotonic()+10
    while not window.initialized:
        _require((time.monotonic()<deadline), ('window-not-ready'))
        xbmc.sleep(25)
    session.start(order,confirmed=True)
    while not window.finished:
        _require((time.monotonic()<expiry), ('menu-test-timeout'))
        window.refresh(); xbmc.sleep(50)
    passed=True
finally:
    try:window.close()
    finally:
        grant.unlink(missing_ok=True)
        xbmcgui.Window(10000).clearProperty('AsterV2Lab.AlbumWindow')
    restored=not rpc('Player.GetActivePlayers',{}) and not read_queue(rpc).song_ids
    path=run/'host-results.json'
    path.write_text(json.dumps(dict(passed=passed,original_queue_restored=restored,capability_removed=not grant.exists())))
    path.chmod(0o600)
    _require((restored), ('recovery-required'))
