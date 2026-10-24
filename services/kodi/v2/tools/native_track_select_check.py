"""Remote OK on owned playlist row, then survive delayed add-on callbacks."""
import os
import xbmc
from queue_reader import read_queue

def require(condition,message):
    if not condition:raise AssertionError(message)

def check(rpc,label,focus,until,press,select):
    require(os.uname().nodename=='AsterTV','hp-only')
    before=read_queue(rpc)
    require(len(before.song_ids)>1 and before.current_index==0,'first-owned-track-required')
    require(focus(400),'transport-origin')
    press('down');until(lambda:focus(600),'track list focus')
    first=label('Container(600).ListItem.Label');press('down')
    until(lambda:label('Container(600).ListItem.Label')!=first,'next row selected')
    select()
    def selected():
        props=rpc('Player.GetProperties',dict(playerid=0,properties=['position','speed']))
        if props.get('position')!=1 or props.get('speed')!=1:return False
        # Kodi updates position before the asynchronous playing-item metadata.
        # Wait for both; an early position alone is not a successful selection.
        item=rpc('Player.GetItem',dict(playerid=0,properties=[]))['item']
        return item.get('type')=='song' and item.get('id')==before.song_ids[1]
    until(selected,'OK plays the owned queued occurrence')
    require(rpc('Player.GetItem',dict(playerid=0,properties=[]))['item']['id']==before.song_ids[1],'same-selected-song-id')
    # Longer than the existing delayed OnStop clear; startup alone is not proof.
    xbmc.sleep(6500)
    after=read_queue(rpc)
    require(after.song_ids==before.song_ids and after.current_index==1,'queue-survives-track-switch')
    require(label('Container(600).ListItem.Property(NowPlaying)')=='true','playing-marker-follows-track')
    press('left');until(lambda:focus(400),'transport after selection')
    select();until(lambda:rpc('Player.GetProperties',dict(playerid=0,properties=['speed']))['speed']==0,'new track pauses')
    until(lambda:label('Control.GetLabel(400)')=='Resume','paused caption restored')
    return True
