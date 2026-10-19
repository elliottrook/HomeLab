# New disposable storage lead — preparation only

Received authoritative main `384410fd9aacb08f5b89600b5fe9b24a42257c3a`
on the October 18 18:30 preparation continuation. Read
`docs/projects/Lab-Scratch-Mirror.md` at that exact commit. This is a new
storage-owner deployment record, not a B60 lease/recovery or model result.
Git-file SHA-256:
`c596f6761e4e81ce64412596faa8d0aa2c320034825f42a0a84c01bd15b7e6de`.

The record describes 3.51 TiB available on a disposable TrueNAS lab mirror,
exported as `192.168.20.40:/mnt/lab/shared`, NFSv4 TCP, to VLAN70 only.
Its 16 MiB synthetic read/write/hash test passed from LXC114's namespace;
Proxmox's management address was correctly refused. No client mounts were
deployed. Both mirror disks have known adverse histories. Shared AUTH_SYS
maps clients to apps:apps; authorized clients can modify one another's files.
Neither this capacity nor mirroring makes it accepted recovery storage.

## B60 applicability and limits

This is a credible alternative to the previously capacity-blocked guest-root
candidate copy, but not an approved or implemented B60 staging path. It can
hold only replaceable public model/runtime artifacts, never credentials,
private A1 cases/answers, accepted recovery copies or sole benchmark evidence.
Storage authorization does not implicitly authorize a B60 mount, new export,
container privilege change or wider firewall/subnet access.

Before choosing it, the platform/storage owner must supply a reviewed path
compatible with unprivileged LXC110. The documented Proxmox management client
is excluded: do not broaden that access to make a host bind mount convenient.
Preserve one staged candidate and headroom. Recheck pinned bytes/hashes after
copy and immediately before load; reject drift or unavailable storage. A
client read-only mount alone cannot prevent other clients rewriting files.
Use an owner-approved immutable/isolated artifact publication or a verified
local copy with adequate capacity; no such publication is claimed here.

Separate cold NFS load time and failures from warm resident inference timing.
Require actual RAM/VRAM residency and no spill, identical measurement boundary
and disclosed cache state. Do not credit remote storage as faster hardware,
claim the 24 GB VRAM limit changed, or treat the small storage test as proof of
20 GB model load stability. Network loss and file mutation must fail closed
without compromising exact accepted SYCL recovery.

## Owner request and unchanged gates

Platform: please assess this existing export as an optional public-artifact
staging path while publishing the changed manual-helper source/install receipt
and corrected independently supervised recovery. Adaptive: retain private
evidence/corpus custody and the same full Aster-path control/candidate boundary.
No policy, permission or numeric qualification bar is changed.

Adaptive remains `92d2237ca91552d9326bb182c2bac0cba01adda7`, platform
`310a0f26c218cb4808d4feb26991fd91fcd76a23`; full-path card and staging
manifest hashes match the October 18 nightly record. No newer READY evidence
was received. The local nightly record is included in this focused liaison
publication, not a new model attempt or a repeated request for ordinary trial
approval. Six unchanged offline recovery-margin tests pass. No LAN host probe,
mount, download, GPU/model call, credential or production mutation occurred.
