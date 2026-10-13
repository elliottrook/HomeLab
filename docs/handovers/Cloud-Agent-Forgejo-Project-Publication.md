# Cloud-Agent Forgejo Project Publication — Local Handover

**Owner:** Jason  
**Date:** 2026-10-13  
**Status:** Stream A continuation; local implementation and recovery gates are
passing; the dedicated writer and project gateway are enabled; the first
Forgejo publication remains pending immediate confirmation.

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
- `3e9ef519` — handover and continuation status

The human root-ceremony, provisioning, deployment and validation helpers are
included in the next local commit. They remain separate from the cloud-agent
surface: the ceremony creates only a temporary human handoff, while the
project gateway supplies the narrowly scoped credential internally.

The local broker suite passes `133/133`. The package verifier is offline and
rejects traversal, symlink, binary, delete/rename, hidden, collision,
secret/private-detail, stale-base, replay and policy-drift cases. Approval
payloads contain metadata and digests only; document bytes remain in the
digest-named local handoff.

## Live evidence and current blocker

- LXC 104 has the protected checkpoint
  `forgejo-project-docs-pre-m2-20261013`.
- The live runner pin was reconciled to the observed Forgejo `main`,
  `da8b0fca9783fb72ca1ac9da9d31a97f971cfb93`, before installation.
- The project gateway is enabled and active at
  `/run/homelab-forgejo-mcp-project-write/gateway.sock` with mode 0660,
  owned by `hlabroker-project-write:hlabroker`.
- The dedicated AppRole file is installed at
  `/etc/homelab-broker/openbao-project-write-approle.json` as root-owned mode
  0640 with group `hlabroker-project-write`; the existing safe-write
  credential was not reused.
- The protected handoff directory is owned by
  `hlabundle:hlabroker-project-write`, mode 2770, beneath a mode-0710 parent.
- The temporary root-token handoff was revoked and removed after provisioning.

## Live provisioning evidence

- Forgejo identity `ai-pam-project-docs` is non-admin and has write mode only on
  `jason/homelab`. Its PAT was created with only `read:repository` and
  `write:repository` scopes and is stored only at
  `secret/data/ai-pam/forgejo-mcp-project-write`.
- OpenBao policy `hlabroker-forgejo-project-write` grants only `read` on that
  exact KV-v2 data path. The AppRole issues 5-minute client tokens with a
  30-minute maximum, has no default policy, binds SecretIDs to
  `192.168.70.10/32`, and uses a reusable protected SecretID because the
  gateway logs in once per MCP request. The SecretID itself never entered
  chat, Git, logs or receipts.
- `agent-cloud-bundle` is already in `operator` state and has the separate
  Yellow `forgejo.write.project-documents` capability. The existing
  `forgejo.write.safe-branch` capability remains separate.
- The live catalog advertises only the synthetic `create_file_batch` tool;
  `create_file` is denied. A valid-shaped request without an approved staged
  handoff is denied before any Forgejo call.
- The full broker regression passes `133/133`. No project document has been
  written to Forgejo by this deployment.

## Human root-ceremony provisioning runbook

This is the repeatable procedure for the one human-only step needed before a
local operator can provision the dedicated project writer. It is deliberately
not a cloud-agent procedure. The role ID, secret ID, recovery shares, root
token and Forgejo token must never be entered into chat, a model prompt, a Git
file, a receipt, a command argument or an ordinary log.

### Preconditions

1. Work from the checked-out repository on the trusted local Mac. Confirm the
   helper is the reviewed copy and that the local checkout is not carrying
   unexpected edits.
2. Have the human ceremony AppRole role ID, AppRole secret ID and two recovery
   shares available in the operator's password manager or other approved
   offline custody. Do not copy them into a terminal command line.
3. Confirm that the existing root-token handoff is absent. The helper refuses
   to overwrite `/run/openbao-human-root-token`.
4. Run the helper from the local terminal:

   ```sh
   ./ops/credential-broker/setup/run-human-root-ceremony.sh
   ```

The wrapper prompts locally with terminal echo disabled. It stores the four
input lines in a mode-0600 temporary file, stages only a non-secret remote
helper, and sends the payload over noninteractive SSH stdin. The remote helper
logs only sanitized progress. It authenticates the AppRole, generates the OTP
with the installed OpenBao CLI, starts a two-share root ceremony, submits the
shares from stdin, decodes the result from stdin, and writes the root token
only to `/run/openbao-human-root-token` as root-owned mode 0600.

### Expected successful output

The terminal should show only status lines of this form:

```text
CEREMONY_TRANSPORT starting
CEREMONY_STARTED threshold=2
CEREMONY_PROGRESS 1/2
CEREMONY_PROGRESS 2/2
CEREMONY_COMPLETE
```

Do not inspect the handoff with `cat`, `less`, `env`, `ps` or an unrestricted
debug command. A non-secret check may confirm only that the file exists and is
root-owned with mode 0600. The handoff is temporary and must be consumed by
the separately approved provisioning step, then removed and revoked as part
of that step.

### Known failure modes and fixes

| Symptom | Cause | Correct response |
|---|---|---|
| Remote output echoes the whole script or prompts behave strangely | A nested remote PTY was used for a script that itself reads a terminal | Use the wrapper's noninteractive SSH transport; do not use `ssh -tt` or remote `/dev/tty` prompts |
| `read: Illegal option -s` | LXC 117 uses POSIX `/bin/sh`, whose `read` has no `-s` option | Keep hidden input in the local wrapper using `stty -echo`; do not add Bash-only syntax to the remote helper |
| `HTTP 400; OTP string has incorrect length` | A hand-built `openssl rand -base64` value is not necessarily the OTP format OpenBao expects | Generate the OTP with `bao operator generate-root -generate-otp -format=json` using the authenticated ceremony operator token |
| `CEREMONY_STARTED threshold=2` followed by rejected shares | OpenBao's CLI treats `-` as stdin, but `-non-interactive` replaces stdin with an empty reader | For share submission and encoded-token decoding, omit `-non-interactive` and pipe the value through stdin. Keep `-non-interactive` for login, status, OTP generation, init and cancellation |
| `CEREMONY_FAILED: could not start root ceremony` | The request was malformed or the OTP had the wrong format/length | Do not retry blindly. Read only the sanitized status, correct the transport/OTP issue, and let the helper cancel the partial ceremony and revoke its operator token |
| `root-token handoff already exists` | A previous ceremony left a protected handoff for an unfinished provisioning step | Stop. Do not overwrite it; complete or explicitly recover the approved provisioning workflow first |
| Forgejo reports `Forgejo is not supposed to be run as root` or cannot load its config | The admin CLI must run as the `git` service user with the installed config and work path | Use `runuser -u git -- forgejo --config /etc/forgejo/app.ini --work-path /var/lib/forgejo ...`; keep the raw PAT in a protected temporary file |
| AppRole readback shows `secret_id_bound_cidrs: null` | OpenBao persists the plural `secret_id_bound_cidrs` field even though other Vault-family examples use a singular list parameter | Write the plural field and read it back before issuing the runtime SecretID; do not start the gateway while it is null |
| A second gateway request fails after the first login | A one-use SecretID is incompatible with this gateway's per-request AppRole login | Use the proven reusable SecretID pattern (`secret_id_num_uses=0`, `secret_id_ttl=0`) while keeping issued client tokens at 5m/30m and the credential file root-owned |
| Service identity cannot access the handoff | The existing bundle-runner parent is mode 0700 | Set only the parent traverse boundary to `hlabundle:hlabroker-project-write` mode 0710 and the dedicated handoff to mode 2770; do not broaden the inbox or ledger |

On any other failure, preserve only the sanitized status. The helper attempts
to cancel an incomplete ceremony, revoke its temporary operator token and
remove its temporary files. It never prints the secret payload. If cleanup
cannot be confirmed, stop before starting another ceremony and have the local
operator inspect the service using the established privileged procedure,
without exposing token values.

## Required local-agent continuation

1. Re-read the current Forgejo `main`, runner source, policy digest and
   protected checkpoint before each candidate package.
2. Stage a signed package into the digest-named handoff. Keep the manifest,
   content and signature local; the broker approval frame carries metadata and
   digests only.
3. Run intake, approval, revoke, expiry, kill-switch, restart and cleanup
   tests. The capability is registered only for the already-promoted
   `agent-cloud-bundle`; do not widen the old canary.
4. Obtain Jason's immediate confirmation for the exact first Forgejo write,
   then create only a new `ai-pam/` branch. Verify the Forgejo branch/tree
   read-only and observe the GitHub mirror read-only.
5. Hold local project commits until the completion gate, then push once to
   Forgejo and verify the derived mirror. Never push GitHub.

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
