# Cloud-Agent Forgejo Project Publication — Local Handover

**Owner:** Jason  
**Date:** 2026-10-13  
**Status:** Stream A continuation; local implementation and recovery gates are
passing; live enablement is waiting on a dedicated writer credential and base
reconciliation.

## Authority and scope

For this project, “git” means Forgejo. Forgejo is the authoritative source of
truth and the only remote that may receive a project publication. GitHub is
Forgejo’s automatic protection mirror and may be checked read-only after a
Forgejo write; no direct GitHub push is permitted.

The cloud agent may have broader read-only repository context through the
existing Green Forgejo path. Write access is unchanged and remains limited to
UTF-8 `.md`, `.markdown` and `.txt` files below:

- `docs/projects/`
- `docs/handovers/`

The package limit is 32 files, 1 MiB per file, 8 MiB total and a 256 KiB
manifest. Larger content is staged locally and is not placed in the small
broker approval frame. No source, tests, infrastructure, CI, workflow,
credential, `main`, tag, release, merge, delete or force operation is in scope.

## Completed local work

The replacement branch is `codex/cloud-agent-forgejo-access`. Its published
Forgejo base is `503deb1155fc933887cc5f111180f52ba74ebf84`; local work is held
for the project-completion push as requested. The current local commits after
that published base are:

- `2fd21c56` — isolated runner preflight record
- `c6de5052` — Stream A authorization record
- `bc4d9055` — bounded project-document capability
- `0183a48` — credential boundary, size policy and protected checkpoint
- `3ba66800` — fail-closed mid-batch recovery behavior and test

The local broker suite passes `132/132`. The package verifier is offline and
rejects traversal, symlink, binary, delete/rename, hidden, collision,
secret/private-detail, stale-base, replay and policy-drift cases. Approval
payloads contain metadata and digests only; document bytes remain in the
digest-named local handoff.

## Live evidence and current blocker

- LXC 104 has the protected checkpoint
  `forgejo-project-docs-pre-m2-20261013`.
- The live runner pin is `d7e49c4d4d6b7124a764208cc44e0ef9ed12797b`.
- The observed Forgejo `main` is
  `da8b0fca9783fb72ca1ac9da9d31a97f971cfb93`; the mismatch must be resolved
  before accepting a package.
- The project gateway is not enabled.
- No dedicated project-write AppRole file exists. The existing safe-write
  credential must not be reused.

## Required local-agent continuation

1. Re-read the current Forgejo `main`, runner source, policy digest and
   protected checkpoint. Reconcile the runner base only after recording the
   exact new value and preserving rollback to the checkpoint.
2. Provision a separate non-admin Forgejo writer identity limited to
   `jason/homelab` and the project branch/write operation. Store its token only
   at the dedicated OpenBao path
   `secret/data/ai-pam/forgejo-mcp-project-write`.
3. Provision the dedicated project gateway AppRole and install its credential
   only at `/etc/homelab-broker/openbao-project-write-approle.json`. Never print,
   copy into a package, commit, receipt, chat message or ordinary log any
   credential value.
4. Run the candidate installer only in the approved M2 window, using the
   literal `--approved-m2-window` guard. Register the capability only for an
   already-promoted `agent-cloud-bundle`; do not widen the old canary.
5. Run synthetic intake, approval, revoke, expiry, kill-switch, restart and
   cleanup tests. Then perform the first Forgejo write only after the immediate
   confirmation required by `AGENTS.md`; create a new `ai-pam/` branch only.
6. Verify the Forgejo branch/tree read-only, then verify the GitHub mirror
   read-only. Hold all local commits until the project completion gate, then
   push once to Forgejo and verify the derived mirror. Never push GitHub.

## Recovery and stop conditions

A later-file failure can leave a partial non-main branch because the upstream
MCP currently receives sequential `create_file` operations. The gateway now
fails closed and never reports success for that state. Preserve the branch and
manifest for audit; do not merge or delete it automatically.

Stop immediately on a credential value appearing in output, a base or policy
mismatch, an unexpected destination, a request outside the two document roots,
any need to write GitHub, any request to change `main`, or any need to widen
the package class. Rollback disables only this new capability and revokes its
dedicated writer/AppRole; it must not disturb the existing read or safe-write
credentials.
