"""Native Menu cancel/on/off check, no server saves or profile changes."""
import os
import xbmc
from queue_reader import read_queue
from music_scrub import clock_milliseconds

def require(condition,message):
    if not condition:raise AssertionError(message)

def check(rpc,label,focus,until,press,select):
    require(os.uname().nodename=='AsterTV','hp-only')
    original=read_queue(rpc)
    require(original.current_index is not None and len(original.song_ids)>1,'owned-playing-queue-required')
    def props():return rpc('Player.GetProperties',dict(playerid=0,properties=['speed','time','shuffled']))
    before=props();require(before['speed']==0 and before['shuffled'] is False,'paused-ordered-origin')
    def choose(yes,title):
        until(lambda:focus(400) and label('Window.Property(Album.ControlHint)')=='Resume','transport ready before Menu')
        press('contextmenu');until(lambda:label('Control.GetLabel(1)')=='Queue actions','Queue menu')
        for _ in range(2):press('down');xbmc.sleep(100)
        select();until(lambda:label('Control.GetLabel(1)')==title,'shuffle confirmation')
        target=next(i for i in (10,11) if label('Control.GetLabel('+str(i)+')')==('Yes' if yes else 'No'))
        if not focus(target):press('right' if target==11 else 'left')
        select();xbmc.sleep(400)
    choose(False,'Shuffle queue')
    require(read_queue(rpc)==original and props()['shuffled'] is False,'cancel-must-not-shuffle')
    choose(True,'Shuffle queue')
    until(lambda:'shuffle on' in label('Window.Property(Album.TrackHeading)'),'visible shuffled queue')
    shuffled=read_queue(rpc);now=props()
    require(now['speed']==0 and now['shuffled'] is True,'native-shuffle-paused')
    require(shuffled.song_ids[shuffled.current_index]==original.song_ids[original.current_index],'same-song')
    require(abs(clock_milliseconds(now['time'])-clock_milliseconds(before['time']))<=500,'clock-not-reset')
    require(label('Container(600).NumItems')==str(len(shuffled.song_ids)),'visible-queue-size')
    require(label('Window.Property(Album.QueueFingerprint)')==shuffled.fingerprint,'visible-queue-exact-native-order')
    choose(True,'Restore queue order')
    until(lambda:'original order' in label('Window.Property(Album.TrackHeading)'),'original queue visible')
    require(read_queue(rpc)==original and props()['shuffled'] is False and props()['speed']==0,'exact-original-restore')
    require(label('Window.Property(Album.QueueFingerprint)')==original.fingerprint,'visible-original-order')
    require(focus(400),'origin-control-restored')
    return True
