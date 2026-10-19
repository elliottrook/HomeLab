# F3/F4 inactive stage result — 2026-10-19

Status: staged and validated; effects remain disabled. This receipt records the
approved inactive Proxmox installation only. It does not authorize F3 receipt
production, F4 evidence production, F6 arming, F7 approval, F8 acquisition,
service stops, model calls, timer changes, daemon reloads, or a remote push.

## Installed paths

| Path | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/pre_acquire_receipt.py` | `7c70b6c8097ec9b5b9d2dd6e980f59a6b15ebd8397fbf5acbced98a2e7cc2170` | `root:root 0644` |
| `/usr/local/libexec/local-ai-lease/full_stop_acquire_candidate.py` | `fb59110ebf8236c67c40818f16f2e501503ebe2740e0eaf9672a5a09174b4ecb` | `root:root 0644` |

The prior controller hash was `5859aba6cccb8f0eb8a971ccc4e3ff7054c1039482f0838c800ed7a10fc0f791`.
Rollback checkpoint: `/root/aster-f3f4-rollback-6309e5f7`, root:root 0700;
the prior controller is root:root 0600 and the checkpoint contains an
absent-target marker for the new pre-acquire module.

## Validation

- Target-Linux compile/import: passed for both installed modules.
- Focused pre-acquire/full-stop suite: 13/13 passed.
- Relevant installed dependency suite: 83/83 passed.
- Repository full suite before staging: 342 passed, 8 expected skips.
- Repository card hash test: passed; all frozen card paths match source bytes.

The first target import attempt omitted the installed `PYTHONPATH` and stopped
before tests or effects; the corrected explicit-path run passed. Two initial
dependency-suite path assertions were corrected in the private test fixture by
including the already-pinned unit files; the rerun passed 83/83.

## Safety postcheck

At completion, the following remained absent:

- `/var/lib/local-ai-lab/archive-integrity.json`
- `/var/lib/local-ai-lab/pre-acquire-receipt.json`
- `/var/lib/local-ai-lab/source-receipt.json`
- `/var/lib/local-ai-lab/lease.json`
- `/var/lib/local-ai-lab/lease.lock`

Both `retained_archive_producer_candidate.py` and
`full_stop_acquire_candidate.py` still report `EFFECTS_ENABLED = False`.
`f2-preflight-prepare-20261020.timer` and
`f2-preflight-final-20261020.timer` remained active/enabled; their services
remained inactive. The private `/tmp/aster-f3f4-stage-6309e5f7` directory was
removed. No service was stopped, no model was called, no receipt or lease was
created, no daemon was reloaded, and no timer was changed.
