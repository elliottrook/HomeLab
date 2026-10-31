#!/usr/bin/env python3
"""Add explicit, progress-backed Resume rows for started podcast episodes."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

TARGET=Path('/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib/books_sync_bridge.py')
CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-v2-r11-podcast-resume-20261030')
EXPECTED='6bc3d940b746f68aaaa3d2be1c75d863d70708ca7efbe42a823e5fb91ca63577'
def sha(data):return hashlib.sha256(data).hexdigest()
def idle():
    request={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1',9090),timeout=3) as client:
        client.sendall((json.dumps(request)+'\n').encode());answer=json.loads(client.recv(4096).decode())
    if answer.get('result') != []:raise RuntimeError('active-player')
def one(text,old,new,label):
    if text.count(old)!=1:raise RuntimeError(label+'-anchor')
    return text.replace(old,new,1)
def main():
    idle();before=TARGET.read_bytes()
    if sha(before)!=EXPECTED:raise RuntimeError('unexpected-live-hash')
    text=before.decode()
    text=one(text,'media=metadata[\'media\'];resume_entry=None',
        "media=metadata['media'];resume_entry=None;podcast_resumes=[]",'resume-list')
    old="""                if kind=='audiobook' and resume_entry is None:
                    progress=book_progress
                    if progress is not None and not progress.finished and progress.position>0:
                        index,offset=resume_target(progress,spans)
                        value=self.clone_resume(entry,item_id,book_inodes[index],offset)
                        # The row identifies the whole-book position, not the
                        # remaining length of whichever file contains it.
                        value['title']='Resume · '+clock_label(progress.position)
                        value['resume_position']=progress.position
                        value['duration']=spans[index].duration-offset
                        self.registry.add(value['url'],Binding(scope,spans,index,offset,True,self.clock()+TTL))
                        resume_entry=value
            if resume_entry:entries.insert(0,resume_entry)
"""
    new="""                if kind=='audiobook' and resume_entry is None:
                    progress=book_progress
                    if progress is not None and not progress.finished and progress.position>0:
                        index,offset=resume_target(progress,spans)
                        value=self.clone_resume(entry,item_id,book_inodes[index],offset)
                        # The row identifies the whole-book position, not the
                        # remaining length of whichever file contains it.
                        value['title']='Resume · '+clock_label(progress.position)
                        value['resume_position']=progress.position
                        value['duration']=spans[index].duration-offset
                        self.registry.add(value['url'],Binding(scope,spans,index,offset,True,self.clock()+TTL))
                        resume_entry=value
                elif kind=='podcast':
                    progress=self.reader.progress(account,kind,item_id,episode)
                    if progress is not None and not progress.finished and progress.position>0:
                        index,offset=resume_target(progress,spans)
                        value=self.clone_resume(entry,item_id,inode,offset)
                        value['title']='Resume · '+clock_label(progress.position)+' · '+entry['title']
                        value['resume_position']=progress.position
                        value['duration']=spans[index].duration-offset
                        value['episode_id']=episode
                        self.registry.add(value['url'],Binding(scope,spans,index,offset,True,self.clock()+TTL))
                        podcast_resumes.append(value)
            if resume_entry:entries.insert(0,resume_entry)
            if podcast_resumes:entries[0:0]=podcast_resumes
"""
    text=one(text,old,new,'podcast-resume')
    after=text.encode();CHECKPOINT.mkdir(mode=0o700);(CHECKPOINT/'books_sync_bridge.py').write_bytes(before)
    (CHECKPOINT/'manifest.json').write_text(json.dumps({'kind':'astertv-v2-r11-podcast-resume',
        'before':sha(before),'after':sha(after)},indent=2,sort_keys=True)+'\n')
    subprocess.run(['systemctl','stop','kodi'],check=True)
    try:
        temp=TARGET.with_suffix('.py.r11');temp.write_bytes(after);os.chmod(temp,0o644);os.replace(temp,TARGET)
    finally:subprocess.run(['systemctl','start','kodi'],check=True)
    print(json.dumps({'checkpoint':str(CHECKPOINT),'bridge':sha(after)},sort_keys=True))
if __name__=='__main__':main()
