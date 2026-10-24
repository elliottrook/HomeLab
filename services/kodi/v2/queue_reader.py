"""Read-only, song-ID-only queue snapshots; never fetch media paths."""
from music_queue import QueueSnapshot


class QueueUnavailable(ValueError):
    pass


def read_queue(rpc, *, page_size=500):
    if type(page_size) is not int or not 1 <= page_size <= 20000:
        raise QueueUnavailable('invalid-queue-read-options')

    def read(method, params=None):
        try:
            return rpc(method, params or {})
        except Exception:
            raise QueueUnavailable('queue-read-failed') from None

    def player():
        active = read('Player.GetActivePlayers')
        if not isinstance(active, list) or len(active)>1:
            raise QueueUnavailable('unsupported-active-player')
        if not active:return None
        entry = active[0]
        if (not isinstance(entry,dict) or entry.get('type')!='audio'
                or type(entry.get('playerid')) is not int):
            raise QueueUnavailable('unsupported-active-player')
        props = read('Player.GetProperties',{'playerid':entry['playerid'],
                                            'properties':['playlistid','position']})
        if (not isinstance(props,dict) or type(props.get('playlistid')) is not int
                or props['playlistid']!=0 or type(props.get('position')) is not int
                or props['position']<0):
            raise QueueUnavailable('unsupported-active-player')
        return (entry['playerid'],props['position'])

    def snapshot():
        before = player()
        ids, expected = [], None
        while True:
            start = len(ids)
            result = read('Playlist.GetItems',{'playlistid':0,
                          'limits':{'start':start,'end':start+page_size}})
            if not isinstance(result,dict):raise QueueUnavailable('incomplete-queue-page')
            limits = result.get('limits'); items = result.get('items',[])
            if (not isinstance(limits,dict) or not isinstance(items,list)
                    or any(type(limits.get(k)) is not int for k in ('start','end','total'))
                    or not 0 <= limits['total'] <= 100000
                    or limits['start']!=start or limits['end']!=start+len(items)
                    or limits['end']>limits['total'] or len(items)>page_size
                    or (expected is not None and expected!=limits['total'])
                    or (not items and limits['end']<limits['total'])):
                raise QueueUnavailable('incomplete-queue-page')
            expected=limits['total']
            for row in items:
                if (not isinstance(row,dict) or row.get('type')!='song'
                        or type(row.get('id')) is not int or row['id']<1):
                    raise QueueUnavailable('unsupported-queue-item')
                ids.append(row['id'])  # Preserve repeated songs and exact order.
            if limits['end']==expected:break
        if player()!=before:raise QueueUnavailable('queue-changed-during-read')
        try:return QueueSnapshot(tuple(ids),before[1] if before else None)
        except ValueError:raise QueueUnavailable('queue-changed-during-read') from None

    first, second = snapshot(), snapshot()
    if first!=second:raise QueueUnavailable('queue-changed-during-read')
    return second
