# SA2 Doctor-status producer release packet — 2026-10-27

Status: **source-complete and independently reviewed; not deployed**

The exact three-file packet at source commit
`c8346ed7ecaa4100ea819a89084608db4a8dc64d` advances only the fixed
`homelab-doctor/status` observation and the decision-binding correction needed
to consume it safely. The manifest contains exact source-to-target candidate
and predecessor mappings; substitutions, mapping swaps, duplicate JSON keys or
authority drift fail closed.

## Packet identity

- manifest SHA-256:
  `d65cab046facf2dde8c985d15401362b8333ea98c35a058114622f488672c641`;
- validator SHA-256:
  `ae4ab788d7ab7af3dea8de5353a9d888e1177e448435050a1da0a7068edd84b8`;
- validator test SHA-256:
  `d1ffc0f02003a3a44703378b8830283add7e24110602ca4e89f704807a1366f8`.

## Validation

- bundle validator: **passed**, three exact files;
- validator regressions: **3/3 passed**;
- underlying dependency-free sysadmin suite: **72/72 passed**;
- independent source and release-packet review: **PASS** after exact mapping
  and predecessor-drift tests were added.

## Remaining release gates

The predecessor hashes come from the latest retained deployment evidence and
must be re-read from LXC104 after the protected backup/timed-test window. The
three candidates then need target-Python tests and an exact rollback installer.
Any deployment restarts Aster Agent and therefore requires a separate immediate
approval. The packet does not restart or change the model, enable automatic
routing, call a model, refresh Doctor or grant repair authority.

