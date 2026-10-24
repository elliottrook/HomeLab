"""HP-only native queue occurrence/remove/clear regression, in-process RPC.

Uses three previously verified song IDs, private expiring test capability,
and a five-occurrence queue. Never touches saved/server playlists.
"""
import json, os, sys, time
from pathlib import Path
import xbmc

assert os.uname().nodename == 'AsterTV'
sys.dont_write_bytecode = True
sys.path.insert(0, '/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_expanded_trial import ExpandedTrial, save_intent
from music_progressive import ProgressiveSession
from music_trial import TrialUnavailable, save_empty_checkpoint, validate_write
from queue_reader import read_queue


def rpc(method, params=None):
    result = json.loads(xbmc.executeJSONRPC(json.dumps(
        dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    assert 'error' not in result, 'native-rpc-failed'
    return result['result']


def private(path, data):
    with path.open('x') as output:
        json.dump(data, output, sort_keys=True)
    path.chmod(0o600)


root = Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
run = root / ('queue-edit-' + str(time.time_ns()))
run.mkdir(mode=0o700)
baseline = read_queue(rpc)
assert not baseline.song_ids and not rpc('Player.GetActivePlayers')
selection = json.loads(Path('/storage/.aster-checkpoints/aster-music-live-trial-20261023/trial-selection.json').read_text())
ids = tuple(selection['song_ids'])
assert len(ids) == len(set(ids)) == 3
order = (ids[0], ids[1], ids[0], ids[2], ids[1])
expiry = time.monotonic() + 180
grant = run / 'grant.json'
private(grant, dict(song_ids=ids, queue_limit=20000, expires_at=int(time.time()) + 180))
writes = []


def transport(method, params):
    if method in ('Playlist.Add', 'Playlist.Insert', 'Playlist.Remove', 'Playlist.Clear',
                  'Player.Open', 'Player.Stop', 'Player.PlayPause'):
        if method not in ('Player.Stop', 'Playlist.Clear'):
            assert time.monotonic() < expiry and grant.exists(), 'expired'
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
        assert time.monotonic() < deadline, 'fill-timeout'
        xbmc.sleep(25)
    assert session.status()['phase'] == 'ready'
    session.select(2)
    session.pause(False)
    before = engine.observe()
    assert before.current_index == 2 and before.song_ids == order
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
        assert len(writes) == count and engine.observe() == before
    checks.append('current occurrence, stale preview and unconfirmed clear rejected without writes')
    count = len(writes)
    after = session.remove(0, expected_queue=before.fingerprint)
    assert after.song_ids == order[1:] and after.current_index == 1
    assert writes[count:] == ['Playlist.Remove']
    assert rpc('Player.GetProperties', dict(playerid=0, properties=['speed']))['speed'] == 0
    checks.append('removal before current preserves same paused song and adjusts occurrence index')
    count = len(writes)
    after = session.remove(3, expected_queue=after.fingerprint)
    assert after.song_ids == order[1:-1] and after.current_index == 1
    assert writes[count:] == ['Playlist.Remove']
    assert session.selected == after.song_ids
    checks.append('later duplicate removed exactly once without reopening or stopping')
    session.clear(expected_queue=after.fingerprint, confirmed=True)
    assert not rpc('Player.GetActivePlayers') and read_queue(rpc) == baseline
    assert session.status()['phase'] == 'cleared' and not session.selected
    checks.append('confirmed stop-and-clear restores original idle empty queue')
    passed = True
finally:
    try:
        session.close()
    finally:
        grant.unlink(missing_ok=True)
    restored = not rpc('Player.GetActivePlayers') and read_queue(rpc) == baseline
    private(run / 'results.json', dict(passed=passed, checks=checks, original_queue_restored=restored,
                                      capability_removed=not grant.exists(), transport='in-process'))
    assert restored, 'recovery-required-do-not-overwrite-queue'
