#!/usr/bin/env python3
"""Expose movie DB IDs on Aster's read-only Recently Added plugin rows."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

TARGET=Path('/storage/.kodi/addons/plugin.video.asterhome/default.py')
CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-v2-r11-recent-movie-identity-20261030')
EXPECTED='c405f37209bb9fd2507c49fc43591c422aba93beae48137cf43881855f15a28b'
def sha(data):return hashlib.sha256(data).hexdigest()
def idle():
    request={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1',9090),timeout=3) as client:
        client.sendall((json.dumps(request)+'\n').encode());answer=json.loads(client.recv(4096).decode())
    if answer.get('result') != []:raise RuntimeError('active-player')
def main():
    idle();before=TARGET.read_bytes()
    if sha(before)!=EXPECTED:raise RuntimeError('unexpected-live-hash')
    text=before.decode();anchor="""    if row['kind'] == 'episode' and type(row.get('episodeid')) is int:
        item.getVideoInfoTag().setDbId(row['episodeid'])
"""
    addition=anchor+"""    if row['kind'] == 'movie' and type(row.get('id')) is int:
        item.getVideoInfoTag().setDbId(row['id'])
        item.setProperty('AsterDbId', str(row['id']))
"""
    if text.count(anchor)!=1:raise RuntimeError('movie-id-anchor')
    after=text.replace(anchor,addition,1).encode()
    CHECKPOINT.mkdir(mode=0o700);(CHECKPOINT/'default.py').write_bytes(before)
    (CHECKPOINT/'manifest.json').write_text(json.dumps({'kind':'astertv-v2-r11-recent-movie-identity',
        'before':sha(before),'after':sha(after)},indent=2,sort_keys=True)+'\n')
    subprocess.run(['systemctl','stop','kodi'],check=True)
    try:
        temp=TARGET.with_suffix('.py.r11');temp.write_bytes(after);os.chmod(temp,0o644);os.replace(temp,TARGET)
    finally:subprocess.run(['systemctl','start','kodi'],check=True)
    print(json.dumps({'checkpoint':str(CHECKPOINT),'default':sha(after)},sort_keys=True))
if __name__=='__main__':main()
