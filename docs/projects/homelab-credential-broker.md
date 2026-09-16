# Project: HomeLab Credential Broker

> Status: proposed
> Owner: Jason
> Proposed: 2026-09-15
> Started: —
> Completed: —
> Stream: **M (Monitored)** — recommended; requires Jason's confirmation before implementation begins (see "Decisions required")

## Purpose and desired outcome

Give an AI agent (Claude Code / a future homelab agent runner) the ability to
run commands against real HomeLab hosts (Proxmox, TrueNAS-like nodes, the
Forgejo box, etc.) over SSH **without the agent process ever holding, seeing,
or being able to exfiltrate a credential**. The user-visible outcome is: "ask
the agent to check on/manage a host" works, and a fully compromised or
prompt-injected agent still cannot read an SSH key or password.

This was prompted by reviewing the HomelabHero project (serversathome/homelabhero),
which uses a three-user privilege-separation + broker pattern for the same
problem. This project adapts that pattern to this HomeLab rather than adopting
the tool wholesale.

## Current state and evidence

- No credential broker currently exists in this HomeLab.
- Existing privileged access model: the Mac mini holds SSH keys/admin access to
network devices directly; a parallel project (laptop admin parity) is
extending equivalent direct access to the laptop by duplicating keys/scope.
- Reference implementation reviewed: HomelabHero (github.com/serversathome/homelabhero),
README-level detail only — three system users (operator, low-priv agent user,
vault-owning user), a sudoers rule restricting the agent to executing exactly
one broker binary as the vault user, and a non-secret registry separated from
a 700-mode vault directory.
- A first-draft, untested broker skeleton (`hb`, `hb-connect`, `setup-vault.sh`,
a sudoers file) has been sketched conversationally and is included with this
project document as a starting candidate — not yet reviewed against live
HomeLab topology, NetBox, or Authentik/Tailscale identity.

## Scope and exclusions

**In scope:**
- Design and stand up a broker (agent user / vault user / sudoers-narrowed
broker script) on a chosen control-plane host.
- Register at least one real HomeLab host (read-only commands only) through
the broker as a proof of concept.
- Document the credential-isolation model in the repo.

**Explicitly out of scope for this project:**
- Replacing or removing the Mac mini's existing direct SSH access.
- The laptop-admin-parity project's key duplication (related, not merged in
here — this project proposes the broker as an *alternative* worth comparing
against that approach, not a silent replacement of it).
- Any production write/mutating command execution through the broker until a
separate milestone explicitly authorizes it.
- Integrating Tailscale ACLs or Authentik as an additional access layer (noted
as a future extension under Architecture, not built here).

## Authority model

- **Registry** (alias → host/user/port): non-secret, lives in this repo,
authoritative for "what hosts does the broker know about."
- **Vault** (alias → private key material): secret, lives only on the
control-plane host filesystem, mode 700, **never committed to Git** — this
repo is not the authority for key material and must never become it.
- **NetBox**: remains authoritative for device/IP/VLAN facts; the registry
references NetBox-known hosts by address but does not duplicate ownership of
that data.

## Architecture and data flows

Three local system users on one control-plane host (candidate: a small
unprivileged LXC on the T5810, matching HomelabHero's model):

- `hlabagent` — runs the agent/Claude session; low-privilege; cannot read the
vault directory.
- `hlabvault` — owns `/var/lib/homelab-broker/vault` (mode 700); the only
identity that can read key material.
- Trust boundary: one sudoers line lets `hlabagent` execute exactly
`/usr/local/bin/hb-connect`, and only as `hlabvault`. No other command, no
other target user.

Flow: agent calls `hb run <alias> "<command>"` → sudo invokes `hb-connect` as
`hlabvault` → `hb-connect` resolves the alias in the non-secret registry,
reads the matching key from the vault, opens `ssh -o BatchMode=yes` to the
target, returns only stdout/stderr to the agent. The agent's context stream
never contains key material.

Future extension (not built in this project): put the control-plane host
behind Tailscale ACLs so it can only reach declared HomeLab subnets, as a
second, independent layer outside the broker itself.

## Privacy and security design

- Least privilege: `hlabagent` has sudo rights to exactly one binary, as
exactly one non-root target user; no wildcard in the sudoers rule.
- Data minimization: registry holds no secrets; only the vault directory does.
**Corrected 2026-09-15** (was inaccurately described as ".gitignore'd at the
repo root"): the vault (`/var/lib/homelab-broker/vault`) is an absolute path
on the control-plane host, not a path inside this repository, so there is
nothing to `.gitignore` here — it never touches Git either way, which is the
actually-load-bearing fact.
- **Known gap, unresolved as of 2026-09-15 — the sudoers rule does not
enforce read-only use.** `hlabagent ALL=(hlabvault) NOPASSWD:
/usr/local/bin/hb-connect` restricts *which binary* `hlabagent` may run as
`hlabvault`, but sudo does not parse or restrict the arguments passed to
that binary. Concretely: (a) `hlabagent` can invoke `hb-connect add <alias>
<user@host>` exactly as freely as `run`/`test` — `hb-connect`'s own source
comment acknowledges this ("keep 'add' gated at the human/CI layer too,
belt-and-braces") but no such gate is implemented anywhere in the sudoers
file or the script itself; and (b) `hb-connect run` execs whatever string
is passed straight to the remote shell with no command allowlist, so
"read-only commands only" is a stated operational policy, not a technical
control enforced by this code. This is a materially weaker enforcement
model than every other AI-facing broker already in this repository (the
Aster ARR stack manager's execution-disabled broker; Aster's read-only,
non-mutating API-token readers), which enforce the no-mutation boundary in
code. **This must be resolved — either a real remote-command allowlist in
`hb-connect run`, or splitting `add` into a separate binary the sudoers
rule does not grant `hlabagent` access to — before M1 stands up the vault
and sudoers rule for real; it does not block adding these files to the
repo as an unimplemented proposal.**
- No public exposure: broker only listens for local sudo invocation; it does
not open a network port.
- Logging: broker should log alias + command invoked (not output, not key
material) for audit; log location and rotation to be decided at
implementation time and checked against HomeLab Doctor integration below.
- Loopback and unregistered-alias targets are refused by the broker by design.

## Pre-start risk assessment

- **Affected systems:** whichever host is chosen as control-plane (proposed:
new LXC on T5810), plus every HomeLab host subsequently registered with the
broker (initially: read-only test target only).
- **Data/users affected:** none directly; this is infrastructure tooling.
- **Confidentiality/secret-handling risk:** primary risk is a flawed sudoers
rule or vault permission that widens the trust boundary — this is the
single highest-consequence mistake possible in this project and must be
checked with `sudo -l -U hlabagent` before any real key is registered.
**A concrete instance of this risk is already known and unresolved as of
2026-09-15** (see Privacy and security design above): the sudoers rule as
drafted does not restrict `hlabagent` to `run`/`test`, and `run` itself has
no command allowlist — closing this is now a graduation blocker, not a
hypothetical to watch for.
- **Availability/integrity risk:** low in read-only phase; a broken broker
simply fails closed (agent can't reach hosts), it doesn't corrupt anything.
- **Irreversible operations:** none in the read-only proof-of-concept phase.
Registering a host generates a *new* keypair — it does not touch or replace
any existing key on the Mac mini or elsewhere.
- **Recovery/rollback:** broker can be fully removed by deleting the two
service users, the vault directory, and the sudoers file; no HomeLab host
state is touched by that rollback.
- **Test strategy:** validate against one low-value, already-known host first
(e.g. a scratch LXC), using only `echo`/read-only commands, before
registering anything production-relevant.
- **Unresolved decisions requiring Jason's acceptance before work starts:**
see "Decisions required" below.

## Decisions required (before implementation)

1. **Stream:** confirm Monitored (recommended) vs. Autonomous.
2. **Control-plane host:** confirm using a new LXC on the T5810 (vs. an
existing host).
3. **Relationship to laptop-admin-parity project:** confirm this is explored
as an alternative/complement, not a replacement, until you decide otherwise.
4. **First registered host:** confirm a specific low-value test target for
the read-only proof of concept.

## Persistence plan

- Registry file and this project document are Git-tracked and durable.
- Vault directory is durable on the control-plane host's filesystem (LXC
rootfs) but intentionally outside Git; back it up via the LXC's own
Proxmox backup schedule, not via this repo.
- No long-running/background job exists yet in this project — nothing to
checkpoint beyond normal milestone commits.

## Milestones

- [ ] M1 — Stand up `hlabagent`/`hlabvault` users and vault directory on the
chosen control-plane host; verify `sudo -l -U hlabagent` shows exactly the
one narrow rule.
- [ ] M2 — Install `hb-connect`/`hb`; register one read-only scratch host;
confirm `hb run <alias> "echo ok"` succeeds and `hlabagent` cannot read
the vault directly (`sudo -u hlabagent cat /var/lib/homelab-broker/vault/*`
must fail).
- [ ] M3 — Document the model in the repo per this project's template;
integration-checklist pass (see below).
- [ ] M4 — Decide graduation vs. further extension (Tailscale ACL layer,
additional hosts, write-command support).

## Validation and evaluation

- Functional: `hb run`/`hb test` succeed against the registered scratch host.
- Least-privilege/denied-action test: confirm `hlabagent` cannot read vault
files, cannot sudo to any command/user other than the one rule, and cannot
run `hb-connect add` (kept operator-only per the standard's broker design).
- Adversarial input: attempt `hb run localhost "..."` and confirm the broker's
loopback refusal fires.
- Restart behavior: confirm sudoers rule and vault permissions survive a
reboot of the control-plane host.

## Observability and maintenance

- **HomeLab Doctor:** add a check for vault directory permissions (should
always be 700, owned by `hlabvault`) and sudoers file integrity — not
applicable yet for broker *service* uptime since it's invoked on demand,
not a daemon.
- Not applicable: metrics/alerting beyond Doctor at this stage (no persistent
service to monitor yet).

## Backup, restore and rollback

- Vault directory: covered by the control-plane LXC's Proxmox backup, not Git.
- Registry + all scripts: covered by normal repo backup/mirroring.
- Rollback: remove sudoers file, delete the two service users and the vault
directory — no effect on any existing HomeLab host.

## Documentation and systems-of-record updates (integration checklist)

- [ ] HomeLab Doctor — add vault-permission/sudoers-integrity check (M3)
- [ ] Monitoring/alerting — not applicable yet, no persistent service
- [ ] Backup and recovery — vault covered by LXC backup schedule (confirm at M1)
- [ ] NetBox — not applicable; broker references existing NetBox-known hosts,
does not add new device records
- [ ] Human wiki — add an operator page describing what the broker is and how
to register/deregister a host (M3)
- [ ] Aster mirror/snapshot — not applicable at this stage
- [ ] Operational reference/runbooks — add broker usage to homelab-reference (M3)
- [ ] Repository documentation — this project doc + architecture note (M3)
- [ ] Diagrams/rack records — not applicable, no physical/topology change
- [ ] Homepage/service discovery — not applicable, broker has no UI/dashboard
- [ ] Authentication/authorization — new local system users only; no
Authentik/SSO integration in this project
- [ ] DNS, certificates, firewall — not applicable, no network-facing service
- [ ] Automation and schedules — not applicable yet (no cron/systemd unit
in this project's scope)
- [ ] Security inventory — record `hlabagent`/`hlabvault` as new local
identities, vault path, and sudoers file added

## Graduation criteria

- M1–M3 complete and validated.
- The known sudoers/command-allowlist gap (see Pre-start risk assessment,
2026-09-15) is closed — `hlabagent` cannot invoke `hb-connect add`, and
`hb-connect run` enforces an actual remote-command allowlist rather than
executing an arbitrary agent-supplied string — before real key material is
ever registered.
- `sudo -l -U hlabagent` reviewed and confirmed minimal by Jason.
- At least one successful, audited read-only broker call against a real
(non-scratch) HomeLab host.
- Decision recorded on relationship to laptop-admin-parity project.
- Rollback tested once in the scratch environment.

## Evidence log

| Date | Action | Evidence | Residual risk |
|------|--------|----------|----------------|
| 2026-09-15 | Reviewed HomelabHero README for credential-isolation pattern | GitHub README, serversathome/homelabhero | None — read-only research |
| 2026-09-15 | Drafted broker skeleton (`hb`, `hb-connect`, `setup-vault.sh`, sudoers file) conversationally | Files attached to this project | Untested; not yet reviewed against live topology |

## Close-out

Not graduated. Awaiting decisions above before M1 begins.
