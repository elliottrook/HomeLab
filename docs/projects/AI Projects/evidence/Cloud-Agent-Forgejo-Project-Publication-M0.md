# Cloud-agent Forgejo project publication — M0 rescission and design record

Date: 2026-10-13

Status: **Design recorded locally; live capability not enabled.**

## User-directed authority convention

For this project, “git” means Forgejo. Forgejo is the authoritative source of
truth and publication target. GitHub is only the automatic mirror and is not an
input, promotion source or direct write target.

## Rescission evidence

The previously developed GitHub-first process was explicitly rescinded. The
remote Forgejo branch `codex/cloud-agent-forgejo-m1` was deleted by the approved
remote operation. A direct Forgejo ref check returned no such branch. The local
copy of that branch was retired after the worktree was moved to the canonical
Forgejo-based branch.

The first read-only check observed the deleted branch on GitHub while the
automatic mirror converged. A subsequent read-only check found the old branch
absent from both remotes. This was treated as mirror lag, not a reason to write
GitHub directly.

The replacement branch `codex/cloud-agent-forgejo-access` was pushed only to
Forgejo after Jason's explicit confirmation. Forgejo and its GitHub mirror now
resolve that branch to the same commit, `d43ca9eea46e39c349090143219eccb167e0ff5e`.

The old project documents and public-staging design are absent from the new
canonical-based worktree. They are not dependencies of the replacement project.

## Replacement decision

The replacement project is [Cloud-agent Forgejo project publication](../Cloud-Agent-Forgejo-Project-Publication.md).
It deliberately expands access only from the existing one-file/4 KiB safe-write
canary to a separately versioned, multi-file project-document package. It does
not widen that existing policy in place and does not create a GitHub-first path.

The initial package boundary is:

- `docs/projects/` and `docs/handovers/` only;
- UTF-8 text only;
- no deletes, renames, symlinks, submodules, binaries, LFS objects or
  executable content;
- at most 32 files, 256 KiB per file and 2 MiB total;
- exact Forgejo base SHA, branch prefix, package digest, expiry, nonce and
  policy digest;
- existing AI-PAM approval, revocation, one-use consumption, OpenBao custody,
  audit and emergency disable remain mandatory;
- new non-main `ai-pam/` branch only, followed by read-only Forgejo and mirror
  verification.

## M0 gate status

| Gate | Result |
|---|---|
| Old Forgejo branch removed | Passed; direct Forgejo check returned absent |
| Old local process branch retired | Passed; local worktree is on the replacement branch |
| GitHub mirror convergence | Passed; old branch absent and replacement branch matches Forgejo at `d43ca9ee` |
| Canonical base and local policy reconciliation | Passed; Forgejo `main` is `da8b0fca`; local policy sources match the canonical checkout; 30 targeted tests pass |
| Live runner source-pin reconciliation | Pending; known stale runner pin remains a deployment blocker |
| Exact public-mirror privacy boundary accepted | Pending Jason's M0 decision |
| Live worker or AI-PAM policy change | Not started and not authorized |

No service, credential, firewall, DNS, workflow, protected branch or GitHub
configuration was changed by this project record. No new remote Forgejo write
is authorized by this evidence record.
