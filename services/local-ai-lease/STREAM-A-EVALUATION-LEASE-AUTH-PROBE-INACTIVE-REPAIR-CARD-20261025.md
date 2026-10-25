# Stream A metadata-only auth probe repair — inactive card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED**

The live exercise preflight is NO-GO because the authenticated probe helper is
missing on LXC110 and the prior probe would call `/v1/chat/completions`. This
repair adds a metadata-only probe and replaces the runner so both are pinned
and verified before another preflight. It authorizes no live exercise, model
inference, consumer mutation, timer change or remote Git operation.

## Exact two-file transaction

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/llama_auth_probe.py` | `/usr/local/libexec/aster-a1/llama_auth_probe.py` | `ABSENT` | `0996e1b565ad24b740997bbfe598065267e20380135a5af41687d0562239cae6` | 0644 |
| `scripts/local-ai/stream_a_evaluation_prepare_only_exercise.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_prepare_only_exercise.py` | `df106ae07754a219e69366faffcfe7cdcd5f83630728a002a3327bad23288821` | `610b963bccacc028401e6656df071e86dfa8c4066028b3e46291d5f3c9e2ec8a` | 0644 |

The helper wrapper `/usr/local/sbin/aster-llama-production-auth-probe` remains
unchanged at its already-pinned hash. Source commit: `66034749`; the runner
replacement is included in that commit. The helper performs only authenticated
`GET /v1/models`, validates the exact accepted GGUF model ID, disables proxy
inheritance and refuses redirects; it never calls a completion endpoint or
prints a key.

## Required inactive sequence

1. Capture root-owned checkpoints for the absent helper target and existing
   runner target, including hashes, modes, owners and no-symlink properties.
   Refuse on drift.
2. Add the helper atomically and replace only the runner atomically, retaining
   root custody and mode `0644`. Do not alter the auth wrapper, observer,
   owner/launcher, watchdog, units, timers, receipt directory or runtime
   state.
3. Run the helper tests and the complete focused exercise/lease/owner/watchdog/
   observer/launcher suite with Python `-B`; require the metadata probe to
   reject unauthenticated/foreign model responses and ensure no completion
   URL is present. Verify the runner's installed pin set includes both files.
4. Run imports, static hashes/modes and inert runner validation. Confirm all
   F6 units/timers remain disabled/inactive and no runtime lease, identity,
   heartbeat, lock, status or receipt exists. Do not call the live helper,
   runner or model endpoint during installation.

## Rollback

On any failure, remove only the newly added helper and restore only the old
runner from its checkpoint, then rehash both targets. Preserve the unchanged
wrapper and all runtime custody. If state is uncertain, retain evidence and
stop for manual reconciliation; never retry automatically.

This card is prerequisite repair for the separate read-only preflight. It does
not authorize the exercise or any inference call.
