# Stream A GitHub protection mirror URL rejection — 2026-10-10

**State:** Forgejo authoritative branch is current; GitHub protection branch is stale. No direct GitHub push, mirror reconfiguration, force synchronization or credential change has occurred. Recovery is a separate remote-change decision.

## Verified observations

- Jason approved one Forgejo push. `origin/refs/heads/codex/aster-stream-a-handoff` accepted `b11a4ec704497d0e15c39402b93581eb5bbcff1a`.
- Repeated read-only `git ls-remote` queries found GitHub's same branch at the previous `69be8ef5e9150a8702a7a531a9c6783773910a3e`. These observations establish a lag, not whether another GitHub branch or tag changed.
- At the same checkpoint, `main` matched on both remotes at `2b5b941ef8d51ee7b91b091e2e5596c21ff99ba2`. The observed protection gap is the Stream A branch; future pushes may also fail until the mirror URL is repaired.
- The GitHub branch tip is an ancestor of the accepted Forgejo tip in this local Git object database, so this branch needs only a forward update. The Forgejo service on LXC 108 runs version 15.0.7 and is active with zero automatic restarts. A source-local, redacted journal projection found a push-mirror failure at 2026-10-11 02:07:44 UTC; the logged reason class was **mirror URL not allowed**. No raw log line, credential, key or complete mirror URL was copied into this record.
- The URL's SSH host is `github-homelab-mirror`. As the Forgejo `git` user, `ssh -G` resolves that alias to `github.com` with SSH port 22 and user `git`; the alias and `github.com` have different effective identity-file settings. The alias itself does not resolve through `getent`, while `github.com` resolves to a public IPv4 address. This supports the inference that Forgejo's URL validation rejects the SSH alias before Git's SSH configuration can resolve it; it does not prove the exact validation branch or that authentication would succeed after a URL change.
- A source-local projection of `/etc/forgejo/app.ini` found no nonempty `[migrations] ALLOWED_DOMAINS` or GitHub block entry. No secret-bearing configuration value was printed. Any other configured mirrors still need to be reconciled before a global configuration change.

## Safety and recovery decision

Forgejo's [v15 mirroring documentation](https://forgejo.org/docs/v15.0/user/repo-mirror/) says push mirrors may force-push remote refs, and an existing push mirror cannot simply be switched to Forgejo-managed SSH authentication. Its [configuration documentation](https://forgejo.org/docs/v15.0/admin/config-cheat-sheet/) says migration URL restrictions also apply to push mirrors. Therefore, neither recreating the mirror nor relaxing a global allowlist is a routine retry. A direct GitHub push is excluded by the repository rule unless Jason explicitly requests mirror recovery.

The preferred investigation is to inspect the existing mirror's **non-secret metadata** through its supported settings interface: exact URL host/scheme, branch filter, sync mode, last error, SSH-auth mode and whether other push/pull mirrors would be affected. Preserve its credential mechanism and current remote refs. Then compare two bounded repair candidates:

1. Use a canonical `github.com` SSH URL while preserving the exact dedicated key, known-host verification and branch filter. This may require mirror replacement and a separately reviewed remote-write/force-push gate.
2. Explicitly permit only the existing alias under Forgejo's URL policy if the installed implementation supports it and the change does not broaden or break other mirrors. Validate that the alias still resolves only to the intended GitHub host. A global allowlist change is not assumed safe.

Before either change: verify the target repository and refs read-only, confirm the expected GitHub ref is an ancestor of Forgejo's branch, enumerate affected mirror refs without reading credentials, and document rollback to the previous mirror configuration. After a specifically approved repair: run one sync and verify the exact GitHub SHA and no unexpected ref changes. Until then, mark protection-mirror synchronization **FAILED/PENDING** while Forgejo remains the sole authority.
