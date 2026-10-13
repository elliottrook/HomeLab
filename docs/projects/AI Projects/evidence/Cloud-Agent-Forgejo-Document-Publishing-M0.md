# Cloud-agent Forgejo document publishing — M0 evidence

> Date: 2026-10-13
>
> Scope: read-only reconciliation and recommendation only
>
> No Forgejo, GitHub, broker, gateway, runner, policy, credential, network or
> production state was changed.

## Local repository baseline

- Checkout: `/Users/jelliott/.codex/worktrees/6a20/homelab`
- Initial status: clean, detached `HEAD`, local `HEAD=2b5b941e`
  (`origin/main` at the same commit in this checkout).
- The local checkout is behind live Forgejo `main`; no local fetch or reset was
  performed. This preserved the user's existing checkout and made the live
  canonical ref the source for reconciliation.
- `docs/Environment-and-Release-Lifecycle.md` is absent locally and absent on
  live Forgejo `main`; `docs/Standards.md` confirms the Project Creation
  Standard is the current governance source.

## Staged branch provenance

Source URL requested by the handoff:

`https://raw.githubusercontent.com/elliottrook/HomeLab/aster-home-eh001-feasibility/docs/projects/Cloud-Agent-Forgejo-Document-Publishing.md`

Read-only GitHub/API evidence:

- Repository visibility: public.
- Branch: `aster-home-eh001-feasibility`.
- Branch tip: `1b5b5a52e7d2425bc4f2ed88052720f2e1cb1dac`.
- GitHub `main`: `da8b0fca9783fb72ca1ac9da9d31a97f971cfb93`.
- Compare result: `ahead`, 3 commits ahead, 0 behind; merge base equals
  `da8b0fca9783fb72ca1ac9da9d31a97f971cfb93`.
- Commits are unsigned and add only these three Markdown files:
  `docs/handovers/Aster-Home-EH-001-Mac-mini-Codex-Handoff.md`,
  `docs/projects/Aster-Home-Feasibility-PoC.md`, and
  `docs/projects/Cloud-Agent-Forgejo-Document-Publishing.md`.
- The branch is therefore a viable staging transport for public-safe documents,
  not an authenticated or canonical source. Its unsigned history and public
  visibility are residual risks.

## Live Forgejo canonical state

Read-only SSH queries to `root@192.168.20.30` reported:

- Hostname: `forgejo`.
- `forgejo` service: `active`.
- Version: `15.0.7+gitea-1.22.0`.
- Listening ports: SSH `22` and HTTP `3000` on the guest; no mutation was
  attempted.
- Bare repository: `/var/lib/forgejo/data/forgejo-repositories/jason/homelab.git`.
- Symbolic HEAD: `refs/heads/main`.
- Canonical main commit: `da8b0fca9783fb72ca1ac9da9d31a97f971cfb93`.
- Main parent: `ee569a7e3ed34f6a0df4ee22f60963afee0b52b9`.
- Main subject/date: `Plan Aster Voice V1 production graduation`, 2026-10-12.
- Connectivity-only `git fsck` returned clean.
- Existing canary refs remain present: `ai-pam/cloud-runner-canary` at
  `5a4d93ee…` and `ai-pam/cloud-runner-canary-2` at `9574d4de…`, consistent
  with the completed runner record's retained-branch limitation.

Read-only `git ls-remote` to GitHub confirmed GitHub `main` at the same
`da8b0fca…` SHA. No GitHub push was attempted.

## Live broker and runner state

Read-only SSH queries through `proxmox` and `pct exec 104` reported:

- LXC 104: `running`.
- `homelab-broker.service`: `active`.
- `forgejo-mcp-gateway.service`: `active`.
- `forgejo-mcp-write-gateway.service`: `active`.
- `homelab-bundle-health.timer`: `active`.
- Broker socket: `/run/homelab-broker/mcp.sock`, mode `0660`, group
  `hlabroker-clients`; approval socket remains group restricted.
- Read gateway socket: mode `0600`, owned by `hlabroker`.
- Write gateway socket: mode `0660`, owned by `hlabroker-write:hlabroker`.
- Broker admin status: `{"audit_events":115,"global_enabled":true}`.
- Bundle health: `status=healthy`, `ledger_integrity=ok`,
  `states={consumed:2,revoked:2}`, one signer principal, policy digest
  `5d97aba0078723583e2df5f54693d0075deb2b1ec6ecc41fe00f826804fb9f69`.
- Live runner base pin: `d7e49c4d4d6b7124a764208cc44e0ef9ed12797b`, stale relative
  to live Forgejo `main=da8b0fca…`.
- The stale pin is a blocker for any runner-based extension. It is not a reason
  to update the runner during M0; update requires its own bounded change and
  validation.

## Source and regression inspection

Read-only source review covered `broker_core.py`, `broker_service.py`,
`mcp_policy_adapter.py`, `forgejo_mcp_gateway.py`, `bundle_verifier.py`,
`bundle_runner.py`, `bundle_reader.py`, their systemd units and the relevant
tests. Confirmed controls include:

- AF_UNIX-only broker transport and kernel peer credentials.
- Canonical payload SHA-256 binding, policy-digest reauthorization, one-use
  consumption, bounded TTLs, revocation and global disable.
- Green reader fixed to `jason/homelab` and six bounded metadata/content tools.
- Separate read/write gateways with OpenBao-held credentials; caller receives
  no Forgejo credential.
- Yellow safe-write adapter limited to `create_file`, base `main`, branch
  prefix `ai-pam/`, path prefix `ai-pam-pilot/`, 4 KiB content and a required
  `AI-PAM pilot:` commit-message prefix.
- Signed runner bundle verifier performs no network, Git, Forgejo, OpenBao or
  broker I/O and caps content at 4 KiB.

Command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s
ops/credential-broker -p 'test_*.py'`

Result: **112 tests in 22.487 seconds — OK**.

## M0 recommendation and gates

### Recommendation

Use a trusted local import of the reviewed GitHub staging branch for the current
large/multi-file document handoff. It is sufficient and least-relaxing because
it adds no runner permission, broker capability, credential, network path or
public Forgejo exposure. Do not treat the GitHub branch as trusted by origin:
review it as untrusted public input at a pinned SHA.

### Required import gates

1. Jason accepts the proposed Stream A risk envelope and this M0 assessment.
2. The package is explicitly classified as safe for public GitHub visibility;
   otherwise use a private human-carried exchange and reopen the design.
3. The local importer pins the exact staging tip and verifies the exact
   merge-base against a fresh Forgejo `main` read.
4. A documentation-only allowlist, file/count/size caps, no-symlink/submodule/
   binary/workflow/configuration rule and secret scan pass.
5. Jason reviews the exact diff and confirms the destination new non-main
   Forgejo branch and intended effect.
6. Immediate explicit confirmation is obtained before the Forgejo push.
7. Forgejo commit/tree/diff is verified, then GitHub mirror advancement is
   checked read-only. No merge or branch deletion is included.

### Exact blockers

- Stream A acceptance and risk decision for this separate project are not yet
  recorded in canonical HomeLab.
- The staged branch is public and unsigned; package-by-package public-content
  classification is mandatory.
- Import limits and the receipt schema/procedure still need an M1 design and
  synthetic denial/recovery test pass.
- The deployed runner base pin is stale and must not be reused for a new
  extension until separately reconciled.
- The requested Environment/Release lifecycle document is absent from both
  local and live canonical records.

### Deferred alternative

Do not widen the pull runner to multi-file document publication in M0. If a
future requirement needs private automated intake, create a new design gate for
manifest/schema, per-file and total caps, documentation path policy, atomic
review, resource quotas, receipt/replay semantics and an explicit permission
change. The existing canary-only contract must remain unchanged until that
gate passes.
