"""Build a stdin-only HP read probe; does not install code or operate the UI.

Generate locally with --output PATH, then explicitly run on the approved HP:
ssh -o BatchMode=yes root@192.168.1.140 python3 - < PATH
Only aggregate evidence is printed; no media paths or library titles exported.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import argparse
import codecs
import inspect
import json
from pathlib import Path
import platform
import socket


def rpc(method, params=None):
    allowed = {'JSONRPC.Introspect','AudioLibrary.GetSongs',
               'Player.GetActivePlayers','Playlist.GetItems'}
    if method not in allowed:
        raise ValueError('Read-only probe method required')
    with socket.create_connection(('127.0.0.1',9090),timeout=20) as connection:
        connection.sendall((json.dumps({'jsonrpc':'2.0','id':1,'method':method,
                                       'params':params or {}})+'\n').encode())
        decoder = codecs.getincrementaldecoder('utf-8')()
        raw = ''
        while True:
            part = connection.recv(65536)
            if not part:
                raise RuntimeError('probe-transport-closed')
            raw += decoder.decode(part)
            while raw.strip():
                raw = raw.lstrip()
                try:
                    reply, end = json.JSONDecoder().raw_decode(raw)
                except ValueError:
                    break
                raw = raw[end:]
                if reply.get('id') == 1:
                    if 'error' in reply:
                        raise RuntimeError('probe-rpc-failed')
                    return reply['result']


def run():
    _require((platform.node() == 'AsterTV'), ('HP lab host required'))
    before = [rpc('Player.GetActivePlayers'),rpc('Playlist.GetItems',{'playlistid':0})]
    fields = rpc('JSONRPC.Introspect',{'filter':{'id':'Audio.Fields.Song','type':'type'}})
    _require(({'albumid','disc','track','duration'} <= set(
        fields['types']['Audio.Fields.Song']['items']['enums'])), ('native-check-failed'))
    rows, expected = [], None
    while True:
        start = len(rows)
        result = rpc('AudioLibrary.GetSongs',{
            'properties':['albumid','disc','track'],
            'limits':{'start':start,'end':start+1000},
            'sort':{'method':'track','order':'ascending'}})
        limits, page = result['limits'], result.get('songs',[])
        _require((all(type(limits.get(k)) is int for k in ('start','end','total'))), ('native-check-failed'))
        _require((limits['start']==start and limits['end']==start+len(page)), ('native-check-failed'))
        _require((0 <= limits['total'] <= 100000 and len(page) <= 1000), ('native-check-failed'))
        _require((limits['end'] <= limits['total']), ('native-check-failed'))
        _require((expected is None or limits['total']==expected), ('native-check-failed'))
        expected = limits['total']
        rows.extend(page)
        if limits['end']==expected:break
        _require((page), ('native-check-failed'))
    _require((len({r['songid'] for r in rows})==len(rows)), ('native-check-failed'))
    albums = {}
    for row in rows:
        if type(row.get('albumid')) is int and row['albumid'] > 0:
            albums.setdefault(row['albumid'],[]).append(row)
    multi = [i for i, tracks in albums.items() if len({r['disc'] for r in tracks}) > 1]
    unknown = [i for i, tracks in albums.items() if all(r['disc']==0 for r in tracks)]
    candidates = list(dict.fromkeys(multi[:3]+unknown[:2]+list(albums)[:3]))
    passed, rejected, multidisc_passed = 0, {}, 0
    for identity in candidates:
        try:
            selection = read_album(rpc,identity,[r['songid'] for r in albums[identity]],page_size=5)
        except AlbumUnavailable as error:
            rejected[str(error)] = rejected.get(str(error),0)+1
            continue
        _require((set(selection.song_ids)=={r['songid'] for r in albums[identity]}), ('native-check-failed'))
        _require((len(selection.tracks)==len(albums[identity])), ('native-check-failed'))
        passed += 1
        multidisc_passed += len({r.disc for r in selection.tracks}) > 1
    after = [rpc('Player.GetActivePlayers'),rpc('Playlist.GetItems',{'playlistid':0})]
    _require((before == after), ('Playback/queue changed during read-only observation'))
    print(json.dumps({'indexed_tracks':len(rows),'indexed_albums':len(albums),
                      'sampled_albums':len(candidates),'ordered_albums':passed,
                      'multidisc_ordered':multidisc_passed,'safe_rejections':rejected,
                      'tracks_without_number':sum(r.get('track')==0 for r in rows),
                      'albums_with_unnumbered_tracks':sum(any(r.get('track')==0 for r in tracks)
                                                         for tracks in albums.values()),
                      'playback_and_queue_unchanged':True}))


def build_probe(output):
    # An explicit generated test artifact, not a source edit or installation.
    module = Path(__file__).resolve().parents[1]/'music_album.py'
    source = ('import codecs,json,platform,socket\n' + module.read_text() + '\n' +
              inspect.getsource(rpc) + '\n' + inspect.getsource(run) + '\nrun()\n')
    compile(source,'<aster-album-read-probe>','exec')
    with Path(output).open('x') as artifact:
        artifact.write(source)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    build_probe(parser.parse_args().output)
