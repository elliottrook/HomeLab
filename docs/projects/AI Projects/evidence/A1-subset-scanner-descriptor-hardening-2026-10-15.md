# A1 private-subset scanner descriptor hardening — 2026-10-15

**Scope:** Offline source and synthetic tests only. No backup job, lease,
model request, deployment, permission change or private-file content was used.

The existing observation helper rejected symlinks seen by `lstat`, but opened
each file by path afterward. A file or nested directory swapped for a symlink
between those operations could redirect the read. The helper now traverses
using directory descriptors, opens entries with `O_NOFOLLOW`, checks device and
inode identity, and rejects file size or timestamp changes during a read. It
also fails closed on platforms without the required descriptor flags.

The output contract is unchanged: only entry count, total bytes, canonical
manifest digest, scan consistency, capture time and `observation-only` claim.
Five scanner tests pass, including deterministic file and directory
replacement before open. The scanner, full-path admission and admitted-batch
test modules pass together (26 tests). `git diff --check` passes.

This reduces accidental and opportunistic path-substitution risk. It does not
authenticate the caller, prevent a malicious owner from fabricating or
restoring content and metadata, or create a source-bound admission receipt.
The A1 live benchmark and full-stop drill remain **NO-GO** under their separate
current-cycle gates.
