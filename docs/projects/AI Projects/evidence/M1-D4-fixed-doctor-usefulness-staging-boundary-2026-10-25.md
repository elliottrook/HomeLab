# M1/D4 fixed Doctor usefulness staging boundary — 2026-10-25

Status: **OFFLINE PASS; TARGET UNCHANGED**

The future fixed Doctor usefulness workload now has an exact inactive staging
manifest for LXC104. It contains only the eight files needed at runtime:

- two exact JSON fixtures/profiles; and
- six dependency-free Python modules, including the explicit runner.

The runtime packet is 29,892 bytes. Its manifest SHA-256 is
`621235c27fae7d0e6055a9d315fd4ef6197a724993ad93bbd89320d43ad9bfcc`.
The target validator SHA-256 is
`88eb7bd866d6db0d874503e42d4e44fc1b4b19d4f041abacb8237e517972e65c`.

The validator requires an exact eight-file set, a root-owned mode-`0700`
directory, root-owned mode-`0600` regular files with link count one, and exact
opened-byte SHA-256 values and total. It rejects extra files, symlinks, digest
drift, authority changes and route enablement. Three staging tests pass; the
complete fixed Doctor usefulness source suite now passes 35/35.

This is an offline boundary only. No file was copied to LXC104, no identity or
unit was created, and no credential, lease, live Doctor observation or model
request was used. A separate exact inactive-install card and approval must
precede staging.

