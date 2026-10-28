# SA1–SA3 Forgejo expansion release preflight — 2026-10-28

## Result

**READY FOR ONE SEPARATELY APPROVED ASTER AGENT RESTART.** The four-source
adaptive candidate now has an exact five-file release, deterministic private
packet, rollback installer and passing disabled target preflight.

## Exact release

- release ID: `sa1-sa3-forgejo-expansion-20261028`;
- manifest SHA-256:
  `323243795ecd945c5eee184057e01df2219daed64892e6d69dd45e030aed4059`;
- packet SHA-256:
  `6e549542fd7892ab81938d89f87bb9e443c721aea3406f074feb4b7cf8c39e24`;
- installer SHA-256:
  `6fa786542b2798dfa7207067e3f8142a93a34b012bfc5af5771bbd0ed62fd4e9`.

The release replaces four exact files and adds only
`forgejo_incident_adapter.py`. Its runtime declaration permits one
`aster-agent.service` restart, no model restart/change, no automatic routing
and no repair authority. The component release suite passes 4/4, the shell
syntax check passes, the broader target application suite passes 80/80 and the
isolated connected candidate run is complete.

## Disabled target preflight

The preflight matched all four live predecessor hashes, confirmed the new
adapter and rollback checkpoint were absent, extracted the exact packet only
under `/tmp`, imported the candidate through LXC104's application environment,
verified the fixed `forgejo-main/git` registration and removed the extracted
candidate. It returned `FORGEJO_EXPANSION_PREFLIGHT_OK`.

Aster Agent remained on PID `26953` with restart count `0`; no live file,
service, model, route or incident database changed. The exact packet and
installer remain inert in Proxmox `/tmp` for the reviewed transaction.

## Rollback

Before replacement, the installer creates a root-only mode-`0700` checkpoint
containing the four exact predecessors. Any failed stage restores those files,
removes the sole new adapter, restarts only Aster Agent and requires exact
health. Successful installation retains the checkpoint for later explicit
rollback.

The remaining gate is Jason's exact restart approval. Installation does not
run another model request; post-install connected validation remains a
separate no-restart step.
