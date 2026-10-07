"""Candidate source-local encrypted delivery on LXC 104; never auto-installed.

Only the reviewed controller may call install after approval. Crypto receives
plaintext through an owned pipe; no secret argv/env or plaintext disk file.
"""
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

NAME='aster-worker-approle'
DESTINATION=Path('/etc/credstore.encrypted')/NAME


def crypto(operation, data):
    args=['/usr/bin/systemd-creds',operation,'--name='+NAME]
    if operation=='encrypt': args.append('--with-key=host')
    elif operation=='decrypt': args.append('--newline=no')
    else: raise ValueError('Unsupported credential operation')
    result=subprocess.run(args+['-','-'],input=data,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,env={'PATH':'/usr/bin:/bin'},timeout=10,check=True)
    if not result.stdout or len(result.stdout)>65536:
        raise ValueError('Invalid credential envelope')
    return result.stdout


def install(packet, *, enabled=False, destination=DESTINATION):
    if enabled is not True: raise ValueError('Credential delivery disabled')
    if (not isinstance(packet,dict) or set(packet)!={'role_id','secret_id','secret_id_accessor'}
            or any(not isinstance(v,str) or not 1<=len(v)<=16384 or
                   any(c.isspace() for c in v) for v in packet.values())):
        raise ValueError('Invalid credential packet')
    destination=Path(destination)
    if not destination.is_absolute() or destination.resolve()!=destination:
        raise ValueError('Invalid credential destination')
    parent=destination.parent.stat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid!=os.geteuid()
            or parent.st_mode & 0o077 or destination.exists()):
        raise ValueError('Destination must be new in a private owned directory')
    plaintext=json.dumps({k:packet[k] for k in ('role_id','secret_id')},sort_keys=True).encode()
    ciphertext=crypto('encrypt',plaintext)
    if crypto('decrypt',ciphertext)!=plaintext:
        raise ValueError('Encrypted credential round trip failed')
    fd,name=tempfile.mkstemp(prefix='.aster-worker-',dir=destination.parent)
    try:
        with os.fdopen(fd,'wb') as output:
            output.write(ciphertext);output.flush();os.fsync(output.fileno())
        # Atomic no-overwrite publication. A concurrent creator wins safely.
        os.link(name,destination)
        directory=os.open(destination.parent,os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        os.unlink(name)
    return True
