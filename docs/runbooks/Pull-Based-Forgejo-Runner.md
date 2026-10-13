# Pull-based Forgejo runner operator guide

> Authority: operator-guide
>
> Reviewed: 2026-10-10
>
> Scope: synthetic one-file branches in `jason/homelab`

## Security boundary

The producer holds the passphrase-protected private key on Jason's Mac. LXC 104
has only the public `cloud-producer` key, an unprivileged `hlabundle` account,
and the existing AI-PAM Yellow `forgejo.write.safe-branch` capability. The
runner has no Forgejo, OpenBao, tailnet or approval credential and cannot connect
directly to either Forgejo gateway socket. No inbound listener exists.

The same identity may use the existing Green `forgejo.read.repository`
capability through `bundle_reader.py`. The broker immediately consumes a
payload-bound Green request, then the independent read gateway applies its
repository/tool/path/argument/output policy using its OpenBao-held read-only
credential. The caller never receives that credential.

Supported read tools are `get_repo`, `list_branches`, `get_file_content`,
`list_repo_contents`, `get_repo_tree` and `list_repo_commits`. The CLI fixes the
repository to `jason/homelab`; file/list paths and refs are explicit, and commit
limits are capped at 100. It cannot invoke issues, pull requests, workflows or
any mutating tool.

The accepted bootstrap exchange is a human-carried directory containing exactly
`request.json`, `request.sig` and `content.txt`. Jason retains each evidence
directory for seven days. The signed request fixes repository, current base,
new `ai-pam/` branch, canary path, content hash/size, policy digest, signer,
nonce and a maximum 15-minute lifetime.

## Submit and approve

1. Verify Forgejo `main`, then update root-owned
   `/etc/homelab-bundle-runner/base_revision`. Never guess or silently rebase.
2. Produce canonical JSON with no trailing newline and sign it interactively:
   `ssh-keygen -Y sign -f ~/.ssh/homelab_change_bundle -n homelab-change-bundle request.json`.
   Never copy, read or log the private key or passphrase.
3. Transfer only the three bundle files into a new mode-`0700`, `hlabundle`-owned
   inbox directory. Run `homelab-bundle-validate@BUNDLE_ID.service` first.
4. Run `bundle_runner.py submit` as `hlabundle`. It creates a pending Yellow
   request but cannot approve or execute it.
5. In Aster Companion, compare the request ID, agent `agent-cloud-bundle`, exact
   path, new branch, effect, rollback and payload hash. Approve only the exact
   matching card. Approval does not write.
6. Obtain immediate explicit confirmation for that exact Forgejo write. Only
   then run `bundle_runner.py promote`; it rechecks signature, expiry, base,
   policy, content and replay state immediately before one broker consume.
7. Verify the Forgejo commit parent, one-file diff and blob SHA-256. Observe the
   GitHub mirror separately. Do not merge or delete the branch without separate
   authorization.

## Read repository content

Run the reader as `hlabundle` through `/run/homelab-broker/mcp.sock`; select
`get_repo`, `list_branches`, or, for example, `get_file_content --path README.md
--ref main`. Green reads need no Companion approval, but every request remains
identity-, capability- and payload-bound and appears in broker audit/history.
Never work around a denial by calling the gateway socket, requesting another
repository or weakening the sensitive-path/output filters.

## States and safe stops

- `pending`: awaiting Companion review; nothing executed.
- `approved`: payload-bound human approval exists; nothing executes until
  `promote` consumes it.
- `expired`: the signed/request lifetime elapsed; regenerate with a new nonce.
- `revoked`: terminally cancelled; it cannot be reopened.
- `consumed`: terminal success; replay is denied.
- `denied`/`rejected`: validation, policy or human review stopped the request;
  investigate metadata and create a fresh bundle rather than mutating it.

Suspend `agent-cloud-bundle` or disable global AI access in Companion for the
fastest intake stop. Disable `homelab-bundle-health.timer` only during documented
maintenance. Direct human Forgejo administration and break-glass remain
independent.

## Health, recovery and revocation

`homelab-bundle-health.timer` runs hourly with a five-minute randomized delay.
The network-denied service checks policy permissions/format, exactly one public
signer, SQLite integrity, state counts and last successful consume age. It emits
metadata only and fails after seven days without a success. Inspect with:

```text
systemctl status homelab-bundle-health.timer
journalctl -u homelab-bundle-health.service
```

Back up only the replay ledger, `allowed_signers`, `base_revision` and
`policy_digest`; Git is authoritative for scripts and units. Never add the
private signing key. Use SQLite's backup API for the live ledger, restore into
an isolated directory, run the health checker against the copies, and prove a
known consumed nonce cannot return to pending and a revoked nonce cannot be
revoked/reopened again. Restore to production only during a documented recovery
after reconciling the ledger high-water state with broker audit and Forgejo.

To revoke signer trust, suspend the agent first, replace/remove the public
principal in the root-owned allowed-signers file, and validate permissions.
Outstanding approvals must also be revoked in Companion. Rotate by adding the
new public identity through a separately reviewed change; never overlap keys by
accident.

## Accepted limitations

- Intake is human-carried, not automatically polled from a private immutable
  exchange.
- The canonical base pin is operator-updated; the worker intentionally has no
  Forgejo read credential.
- Scope remains a single UTF-8 file under `ai-pam-pilot/cloud-runner/` on a new
  `ai-pam/` branch. It cannot merge, publish, deploy or delete.
- Existing LXC 104 Beszel/NetBox coverage is reused. The hourly systemd failure
  is locally observable; proactive push notification is a future enhancement.
- Canary branches are retained until separately authorized cleanup.
