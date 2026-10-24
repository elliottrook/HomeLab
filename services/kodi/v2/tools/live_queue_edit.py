"""HP-only native queue occurrence/remove/clear regression, in-process RPC.

Uses three previously verified song IDs, private expiring test capability,
and a five-occurrence queue. Never touches saved/server playlists.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import json, os, sys, time
from pathlib import Path
import xbmc

_require((os.uname().nodename == 'AsterTV'), ('native-check-failed'))
sys.dont_write_bytecode = True
sys.path.insert(0, '/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_expanded_trial import ExpandedTrial, save_intent
from music_progressive import ProgressiveSession
from music_trial import TrialUnavailable, save_empty_checkpoint, validate_write
from queue_reader import read_queue


def rpc(method, params=None):
    result = json.loads(xbmc.executeJSONRPC(json.dumps(
        dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    _require(('error' not in result), ('native-rpc-failed'))
    return result['result']


def private(path, data):
    with path.open('x') as output:
        json.dump(data, output, sort_keys=True)
    path.chmod(0o600)


root = Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
run = root / ('queue-edit-' + str(time.time_ns()))
run.mkdir(mode=0o700)
baseline = read_queue(rpc)
_require((not baseline.song_ids and not rpc('Player.GetActivePlayers')), ('native-check-failed'))
_require((not any(rpc('XBMC.GetInfoLabels',dict(labels=[
    'Window(Home).Property(AsterV2Lab.'+name+')' for name in ('Window','AlbumWindow','TrialRecovery')])).values())),
    'another-pilot-or-recovery-is-active')
selection = json.loads(Path('/storage/.aster-checkpoints/aster-music-live-trial-20261023/trial-selection.json').read_text())
ids = tuple(selection['song_ids'])
_require((len(ids) == len(set(ids)) == 3), ('native-check-failed'))
order = (ids[0], ids[1], ids[0], ids[2], ids[1])
expiry = time.monotonic() + 180
grant = run / 'grant.json'
private(grant, dict(song_ids=ids, queue_limit=20000, expires_at=int(time.time()) + 180))
writes = []


def transport(method, params):
    if method in ('Playlist.Add', 'Playlist.Insert', 'Playlist.Remove', 'Playlist.Clear',
                  'Player.Open', 'Player.GoTo', 'Player.Stop', 'Player.PlayPause'):
        if method not in ('Player.Stop', 'Playlist.Clear'):
            _require((time.monotonic() < expiry and grant.exists()), ('expired'))
        validate_write(method, params, frozenset(ids), queue_limit=20000)
        writes.append(method)
    return rpc(method, params)


engine = ExpandedTrial(transport, ids, lambda s: save_empty_checkpoint(run / 'baseline.json', s),
                       queue_limit=20000, intent=lambda s, **kw: save_intent(run / 'intent.json', s, **kw))
session = ProgressiveSession(engine)
passed = False
checks = []
try:
    session.start(order, confirmed=True)
    deadline = time.monotonic() + 15
    while session.status()['writer_active']:
        _require((time.monotonic() < deadline), ('fill-timeout'))
        xbmc.sleep(25)
    _require((session.status()['phase'] == 'ready'), ('native-check-failed'))
    session.select(2)
    session.pause(False)
    before = engine.observe()
    _require((before.current_index == 2 and before.song_ids == order), ('native-check-failed'))
    for operation in (lambda: session.remove(2, expected_queue=before.fingerprint),
                      lambda: session.remove(0, expected_queue='stale'),
                      lambda: session.clear(expected_queue=before.fingerprint)):
        count = len(writes)
        try:
            operation()
        except TrialUnavailable:
            pass
        else:
            raise AssertionError('unsafe-edit-accepted')
        _require((len(writes) == count and engine.observe() == before), ('native-check-failed'))
    checks.append('current occurrence, stale preview and unconfirmed clear rejected without writes')
    count = len(writes)
    after = session.remove(0, expected_queue=before.fingerprint)
    _require((after.song_ids == order[1:] and after.current_index == 1), ('native-check-failed'))
    _require((writes[count:] == ['Playlist.Remove']), ('native-check-failed'))
    _require((rpc('Player.GetProperties', dict(playerid=0, properties=['speed']))['speed'] == 0), ('native-check-failed'))
    checks.append('removal before current preserves same paused song and adjusts occurrence index')
    count = len(writes)
    after = session.remove(3, expected_queue=after.fingerprint)
    _require((after.song_ids == order[1:-1] and after.current_index == 1), ('native-check-failed'))
    _require((writes[count:] == ['Playlist.Remove']), ('native-check-failed'))
    _require((session.selected == after.song_ids), ('native-check-failed'))
    checks.append('later duplicate removed exactly once without reopening or stopping')
    session.clear(expected_queue=after.fingerprint, confirmed=True)
    _require((not rpc('Player.GetActivePlayers') and read_queue(rpc) == baseline), ('native-check-failed'))
    _require((session.status()['phase'] == 'cleared' and not session.selected), ('native-check-failed'))
    checks.append('confirmed stop-and-clear restores original idle empty queue')
    passed = True
finally:
    try:
        session.close()
    finally:
        grant.unlink(missing_ok=True)
    restored = not rpc('Player.GetActivePlayers') and read_queue(rpc) == baseline
    private(run / 'results.json', dict(passed=passed, checks=checks, checks_enforced=True,
                                      python_optimization=sys.flags.optimize,original_queue_restored=restored,
                                      capability_removed=not grant.exists(), transport='in-process'))
    _require((restored), ('recovery-required-do-not-overwrite-queue'))
