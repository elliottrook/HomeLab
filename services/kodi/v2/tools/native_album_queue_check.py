"""HP album Menu edits, exact duplicate occurrences; no server playlist writes."""
import os
import xbmc
from queue_reader import read_queue, QueueUnavailable

def require(condition,message):
    if not condition:raise AssertionError(message)

def check(rpc,label,focus,until,press,select):
    require(os.uname().nodename=='AsterTV','hp-only')
    initial=read_queue(rpc)
    require(initial.current_index==1 and len(initial.song_ids)>3,'paused-second-song-required')
    require(rpc('Player.GetProperties',dict(playerid=0,properties=['speed']))['speed']==0,'paused-required')
    def confirm(title,yes):
        until(lambda:label('Control.GetLabel(1)')==title,'confirmation '+title)
        target=next(i for i in (10,11) if label(f'Control.GetLabel({i})')==('Yes' if yes else 'No'))
        if not focus(target):press('right' if target==11 else 'left')
        select()
    def menu(title,index):
        press('contextmenu');until(lambda:label('Control.GetLabel(1)')==title,'menu '+title)
        for _ in range(index):press('down');xbmc.sleep(80)
        select()
    def same(ids):
        try:current=read_queue(rpc)
        except QueueUnavailable as error:
            if str(error)=='queue-changed-during-read':return False
            raise
        return current.song_ids==ids and current.current_index==initial.current_index
    press('down');until(lambda:focus(600),'track list')
    press('down')
    until(lambda:label('Container(600).ListItem.Property(SongId)')==str(initial.song_ids[2]),'third row')
    menu('This track',3);confirm('Remove queued song',True)
    removed=initial.song_ids[:2]+initial.song_ids[3:]
    until(lambda:same(removed),'remove exact nonplaying occurrence')
    until(lambda:label('Window.Property(Album.QueueFingerprint)')==read_queue(rpc).fingerprint,'removed queue rendered')
    # Owner reselects the playing row after rebuilding its queue view.
    menu('This track',2)
    appended=removed+(removed[1],)
    until(lambda:same(appended),'append one selected song, preserving pause/order')
    until(lambda:label('Window.Property(Album.QueueFingerprint)')==read_queue(rpc).fingerprint,'append rendered')
    menu('This track',1)
    inserted=appended[:2]+(appended[1],)+appended[2:]
    until(lambda:same(inserted),'Play Next inserts one duplicate after current')
    until(lambda:label('Window.Property(Album.QueueFingerprint)')==read_queue(rpc).fingerprint,'Play Next rendered')
    menu('This track',3)
    until(lambda:label('Control.GetLabel(1)')=='Keep playing song','playing occurrence removal refused')
    press('back');until(lambda:label('Control.GetLabel(1)')!='Keep playing song' and focus(600),'refusal returns to track')
    xbmc.sleep(400)  # Let the modal's Back guard expire before opening Menu.
    require(same(inserted),'refused removal leaves queue unchanged')
    press('left');until(lambda:focus(400),'transport menu')
    menu('Queue actions',3);confirm('Stop and clear queue',False);xbmc.sleep(400)
    require(same(inserted),'cancelled clear unchanged')
    menu('Queue actions',3);confirm('Stop and clear queue',True)
    def empty():
        if rpc('Player.GetActivePlayers'):return False
        try:return not read_queue(rpc).song_ids
        except QueueUnavailable as error:
            if str(error)=='queue-changed-during-read':return False
            raise
    until(empty,'confirmed clear stops and empties owned queue')
    until(lambda:label('Window.Property(Album.ControlHint)')=='Play','clear worker joined')
    return True
