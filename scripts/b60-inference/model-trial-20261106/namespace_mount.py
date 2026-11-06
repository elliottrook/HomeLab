"""Linux x86_64 detached read-only mount transfer; child-process use only.

No shell, credentials, namespace creation or implicit fallback. Caller binds
source/target identities and owns durable intent before calling. Source custody
and child namespace identity must be verified separately by the fixed adapter.
"""
import ctypes
import os
import platform
import stat
from pathlib import Path


class MountError(RuntimeError): pass
libc=ctypes.CDLL(None,use_errno=True)


def checked(value):
    if value<0: raise MountError('MOUNT_SYSCALL_'+str(ctypes.get_errno()))
    return value


def identity(path):
    s=os.stat(path,follow_symlinks=False)
    if not stat.S_ISDIR(s.st_mode): raise MountError('MOUNT_DIRECTORY_REQUIRED')
    return (s.st_dev,s.st_ino)


def private_target_parent(raw,target):
    rows=[]
    for line in raw.splitlines():
        fields=line.split()
        if len(fields)<10 or '-' not in fields:raise MountError('MOUNTINFO_MALFORMED')
        mount=fields[4]
        if target==mount or target.startswith(mount.rstrip('/')+'/'):
            rows.append(fields)
    if not rows:raise MountError('TARGET_PARENT_UNKNOWN')
    length=max(len(row[4]) for row in rows)
    return all(not any(v.startswith('shared:') for v in row[6:row.index('-')])
               for row in rows if len(row[4])==length)


def transfer(source,target,pid,*,production_pid=None):
    if platform.machine()!='x86_64':raise MountError('MOUNT_ARCHITECTURE')
    if production_pid is None:
        if not private_target_parent(Path('/proc/'+str(pid)+'/mountinfo').read_text(),target):
            raise MountError('SHARED_TARGET_PARENT_REFUSED')
    elif os.readlink('/proc/'+str(pid)+'/ns/mnt')==os.readlink('/proc/'+str(production_pid)+'/ns/mnt'):
        raise MountError('PRODUCTION_NAMESPACE_REFUSED')
    ns=os.open('/proc/'+str(pid)+'/ns/mnt',os.O_RDONLY|os.O_CLOEXEC)
    rootfd=os.open('/proc/'+str(pid)+'/root',os.O_PATH|os.O_DIRECTORY|os.O_CLOEXEC)
    infofd=os.open('/proc/'+str(pid)+'/mountinfo',os.O_RDONLY|os.O_CLOEXEC)
    targetfd=-1;tree=-1
    try:
        tree=checked(libc.syscall(ctypes.c_long(428),ctypes.c_int(-100),
            ctypes.c_char_p(os.fsencode(source)),ctypes.c_uint(1|os.O_CLOEXEC)))
        class Attr(ctypes.Structure):
            _fields_=[('attr_set',ctypes.c_uint64),('attr_clr',ctypes.c_uint64),
                      ('propagation',ctypes.c_uint64),('userns_fd',ctypes.c_uint64)]
        attr=Attr(1|2|4|8,0,1<<18,0) # readonly,nosuid,nodev,noexec
        checked(libc.syscall(ctypes.c_long(442),ctypes.c_int(tree),ctypes.c_char_p(b''),
            ctypes.c_uint(0x1000),ctypes.byref(attr),ctypes.c_size_t(ctypes.sizeof(attr))))
        checked(libc.setns(ctypes.c_int(ns),ctypes.c_int(0)))
        os.fchdir(rootfd);os.chroot('.');os.chdir('/')
        if production_pid is not None:
            # Standard unshare isolation step, confined to the already-proven
            # distinct candidate namespace. Propagation changes do not alter
            # peer mounts in production; refuse if the resulting parent shares.
            checked(libc.mount(ctypes.c_void_p(0),ctypes.c_char_p(b'/'),ctypes.c_void_p(0),ctypes.c_ulong((1<<14)|(1<<18)),ctypes.c_void_p(0)))
            raw=os.read(infofd,1024*1024+1)
            if len(raw)>1024*1024 or not private_target_parent(raw.decode(),target):raise MountError('PRIVATE_CANDIDATE_PARENT_UNVERIFIED')
        targetfd=os.open(target,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        checked(libc.syscall(ctypes.c_long(429),ctypes.c_int(tree),ctypes.c_char_p(b''),
            ctypes.c_int(targetfd),ctypes.c_char_p(b''),ctypes.c_uint(0x4|0x40)))
    finally:
        if tree>=0:os.close(tree)
        if targetfd>=0:os.close(targetfd)
        os.close(infofd);os.close(rootfd);os.close(ns)


def remove(target,pid,expected):
    # Resolve only inside the target root after entering its mount namespace.
    ns=os.open('/proc/'+str(pid)+'/ns/mnt',os.O_RDONLY|os.O_CLOEXEC)
    rootfd=os.open('/proc/'+str(pid)+'/root',os.O_PATH|os.O_DIRECTORY|os.O_CLOEXEC)
    try:
        checked(libc.setns(ctypes.c_int(ns),ctypes.c_int(0)))
        os.fchdir(rootfd);os.chroot('.');os.chdir('/')
        if identity(target)!=tuple(expected):raise MountError('FOREIGN_MOUNT_RETAINED')
        if not os.statvfs(target).f_flag & os.ST_RDONLY:raise MountError('MOUNT_NOT_READONLY')
        checked(libc.umount2(ctypes.c_char_p(os.fsencode(target)),ctypes.c_int(0)))
    finally:os.close(rootfd);os.close(ns)
