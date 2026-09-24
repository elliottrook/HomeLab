# MacBook administration layer

> Owner: Jason
> Proposed: 2026-09-24
> Status: Proposed — project creation only; implementation not started
> Stream: A requested; execution scope and risk assessment below await acceptance
> Charter: [Project Creation Standard](../Project-Creation-Standard.md)

## 1. Purpose and desired outcome

Equip Jason’s MacBook with an independent copy of the HomeLab administration
capabilities currently used on the Mac mini. Jason can operate the lab directly
from either Mac, without AI, Screen Sharing, the other Mac or an external disk.
The mini remains the always-on scheduled administration and GPT mobile host.

Keep both workspaces on their respective internal SSDs. Jason explicitly
removed external-SSD migration from scope after the size assessment. No new
always-on node is required. A second working environment provides resilience;
it does not replace versioned backups.

## 2. Current state and evidence

- Mac mini: M4, 16 GB, macOS 26.6.2, current address `192.168.1.206`, local name
  `Jasons-Mac-mini.local`. Automatic system sleep is disabled; display sleep is
  ten minutes. Jason confirmed native MacBook Screen Sharing works.
- MacBook: user-supplied screenshot identifies a 15-inch M2 Air (2023), 16 GB,
  macOS Tahoe 26.5.2. No serial number is retained. Direct tool installation,
  shell configuration, credentials, FileVault and backup state are not verified.
- iPhone/iPad full-desktop use was rejected for usability. GPT Remote through
  the mini remains the mobile workflow. See [remote administration](Mac-Remote-Administration.md).
- The active mini command resolves to `~/lab/homelab/scripts/lab`. A different
  legacy `~/lab/bin/lab` contains obsolete addresses: do not replicate it.
- `scripts/lab` assumes `$HOME/lab/homelab`. Doctor supports selected environment
  overrides but uses `$HOME/lab/private-backups` for backup checks and maintains
  local counters. Portable installation requires a deliberate host profile.
- Existing mini LaunchAgents include Doctor/report, weekly backups, Aster lab
  worker and knowledge review. None should be blindly copied or enabled on the
  MacBook.
- TrueNAS pulls the mini’s private exports using a dedicated restricted account
  and ACL rooted at `~/lab/private-backups`. That relationship remains unchanged.
- The configured `aster-knowledge-mirror` local workspace directory was absent;
  verify actual source/mirror requirements instead of creating a false authority.

Read-only allocated-space assessment on 2026-09-24: `~/lab` is about **483 MiB**,
including the 433 MiB HomeLab checkout, 19 MiB CAD directory, 1 MiB reference,
0.3 MiB wiki and 29.6 MiB private backups. The checkout includes **369 MiB of
rebuildable AsterCompanion build output** and about 50 MiB Git history. Core lab
files excluding that build tree total approximately 114 MiB. Do not sum nested
figures twice or assume the backup/build files must all be duplicated.

Broader shared resources measured separately: `.codex` 1.84 GiB, `.local` 1.32 GiB,
ChatGPT app 1.35 GiB and VS Code 0.89 GiB. These are not wholly lab resources and
are not a migration list. The internal container has approximately 204 GiB free.
Measurements are allocated sizes, not a forecast or guaranteed reclaimable space.
No data was removed or moved; growth depends on future builds and projects.

## 3. Scope, exclusions and authorization

The current request is to write the project. Implementation begins only after
acceptance of this Stream A scope and risk assessment under the charter.

Bounded implementation covers:

1. Read-only discovery on the two named Macs and established lab targets,
   avoiding secret-bearing output; enumerate exact capabilities and dependencies.
2. Versioned, idempotent MacBook bootstrap and machine-specific configuration;
   install necessary tools from official sources while preserving existing setup.
3. Independent local Git checkouts and offline documentation under MacBook
   `~/lab`; canonical toolkit installation and safe command resolution.
4. A separate passphrase-protected MacBook SSH key generated on that Mac, with
   only its public key enrolled on the enumerated existing administration
   accounts. Keep privileges no broader than the capabilities accepted in M0.
5. Service bookmarks, existing password-manager/sign-in paths, verified server
   trust and narrowly scoped credentials for mandatory diagnostic integrations.
6. Explicit mini/MacBook execution roles, per-host diagnostic state and accurate
   backup-report handling; no duplicate production workers or scheduled actions.
7. Targeted tests, protected bootstrap/recovery documentation and integration
   records in the existing knowledge repositories.

Stream A does not waive platform prompts, local authentication or filesystem
permissions. The repository’s immediate remote-write confirmation rule still
applies, including remote public-key enrollment and Git pushes, unless the user
has explicitly authorized the specific operation. Forgejo is the ordinary push
target; GitHub is verified read-only after automatic mirroring.

Excluded: external-SSD changes; new nodes; moving mini files; whole home/Keychain,
`.ssh`, browser-profile or AI-session copying; private-key transfer; general
credential exports; new root privileges; public ingress or broader firewall
rules; Tailscale rollout; OS upgrades; purchases; changing backup retention or
existing protected pull scope; enabling duplicate MacBook automation. GPT on the
MacBook is optional separate sign-in, not necessary for administration acceptance.

## 4. Authority model

Forgejo owns accepted source history. Each Mac has its own working tree; preserve
uncommitted, untracked and unpushed work explicitly. Use per-host branches and
normal Git review/merge, never shared `.git` folders, iCloud working-tree sync or
bidirectional rsync. GitHub remains the protection mirror.

Live systems own current operational facts; NetBox owns adopted device/address
facts; operational reference and wiki retain their declared roles; Aster knowledge
is derived. Host profiles own local paths/roles. Existing secret custody remains
in force, and machine-specific SSH private keys stay on their generating Mac.

## 5. Architecture and data flows

Each Mac: internal toolkit/docs → existing LAN SSH/HTTPS endpoints. The MacBook
must work without the mini forwarding traffic, supplying keys, sharing files or
hosting a desktop session. Existing LAN trust boundaries remain unchanged.

| Capability | Mac mini | MacBook |
|---|---|---|
| Toolkit and source/docs | Existing internal working copies | Independent internal clones |
| SSH identity | Existing identity | Separate protected identity |
| Human browser administration | Existing sign-ins | Own sign-ins via approved custody |
| Doctor/status checks | Existing production role | On-demand, host-specific state |
| Scheduled reports/backups/Aster worker | Sole normal executor | Disabled/not installed as jobs |
| Private export staging | Existing protected root | No blanket duplication |
| Recovery instructions | Offline internal copy | Offline internal copy |

Diagnostic profiles must distinguish unavailable local mini backup files from
actual production backup failure. Use approved read-only authoritative reports
where available; do not falsely report PASS or quietly disable required checks.
MacBook still shares the lab network/identity infrastructure failure domains;
physical device independence is not complete disaster independence.

## 6. Privacy and security design

Verify FileVault and existing account protection before provisioning credentials.
Generate the MacBook key locally, user-controlled passphrase entry only; keep
private material out of chat, Git and logs. No SSH agent forwarding by default.
Verify host-key fingerprints through the established mini path before trusting
new MacBook connections. Record identity labels and custody references, not values.

For API-based Doctor checks, prefer existing broker capabilities or independent
least-privilege service credentials through supported provisioning. Never copy
all mini tokens to make a test pass. Record unsupported checks and resolve required
coverage explicitly. Maintain password-manager recovery independent of the mini.

Human administration access does not grant AI new authority. Any optional AI
service integration must satisfy the charter’s identity, broker, risk-class,
custody, revocation and break-glass requirements before use.

## 7. Pre-start risk assessment

| Risk | Likelihood / impact | Controls and remaining limitation |
|---|---|---|
| Lost MacBook exposes administration access | Medium / high | FileVault verification, protected unique key, lock policy and revocation runbook; unlocked sessions remain sensitive |
| Existing MacBook configuration overwritten | Medium / medium | Inventory first; backups, managed snippets and conflict detection; no whole-file replacement |
| Wrong/legacy toolkit installed | Medium / high | Canonical repo source, version check and actual shell resolution validation |
| Concurrent edits lose source work | Medium / high | Preserve dirty work, independent branches, no file-sync of working trees |
| Duplicate jobs or alerts | Medium / high | MacBook on-demand role, schedules and worker absent; test denied mutating/scheduled paths |
| Doctor gives misleading backup status | Medium / high | Host profiles and authoritative reports; distinguish unavailable evidence from unhealthy service |
| Credentials gain unnecessary privileges | Medium / high | Exact per-target access manifest, independent identities and deny/revocation tests |
| MacBook remains dependent on mini/Forgejo | Medium / high | Offline docs/local code, local credentials, mini-unavailable and source-service-unavailable validation |

No production downtime intended. Key enrollment is additive and must not remove
working access. No firewall/DNS/certificate changes planned. Stop on unexpected
privilege requirements, changed targets, backup failure, exposed secrets or any
non-waivable charter condition. Local permissions and remote-write gates remain.

Recommended design: independent internal workspaces, unique key, shared accepted
Git history and mini-only automation. Alternative is continuing Screen Sharing,
which is simpler but depends on the mini. New hardware/SSD migration is excluded.
Before execution accept this envelope and identify the MacBook local session,
exact access targets and protected configuration checkpoint during M0.

## 8. Persistence and resumability

Record each milestone’s host identity, installed versions, source commit, managed
paths, credential identifiers, tests, rollback and next safe action. Do not retain
private keys, auth tokens, raw config exports or secret-bearing transcripts.
Bootstrap must detect existing configuration and stop on conflicts. Incomplete
setup is not a successful replica. On resume re-read charter, this project, Git
status and live evidence; never replay uncertain remote writes automatically.

Current checkpoint: proposed project only. No MacBook installation or access
change has occurred. User asked for project creation, not implementation now.

## 9. Milestones

### M0 — Baseline and accepted access manifest

- [ ] Accept Stream A scope/risks and establish an authorized MacBook session.
- [ ] Inventory OS/tools, shell resolution, FileVault, network path and backup.
- [ ] Enumerate required SSH targets/accounts, web services, diagnostic APIs,
  dependencies and current permission classes; identify remote-write gates.
- [ ] Preserve existing MacBook configuration and source/dirty-work checkpoints.
- [ ] Resolve missing knowledge-mirror requirements without inventing authority.

### M1 — Repeatable local toolkit and knowledge

- [ ] Create bootstrap/manifest with pinned or recorded supported dependencies.
- [ ] Clone required repos to MacBook internal storage; preserve mini-only work.
- [ ] Canonical `lab` is selected in a normal interactive shell; stale launcher
  cannot shadow it; bookmarks and offline recovery docs are accessible.
- [ ] Dependency/permission errors give actionable output without secrets.

### M2 — Independent human access

- [ ] Generate unique protected MacBook key and record public fingerprint.
- [ ] Enroll public key on exact approved targets with required confirmations;
  verify host trust and read-only commands without using mini credentials.
- [ ] Establish required browser/password-manager and diagnostic access.
- [ ] Document individual identity revocation and prove relevant denied actions.

### M3 — Diagnostic parity and execution ownership

- [ ] Separate local counters/state and mini-only jobs; no automatic MacBook alerts.
- [ ] Doctor required checks use valid evidence; unsupported checks are resolved
  or explicitly accepted, never silently marked healthy.
- [ ] Two independent functional passes per Mac compare against baseline failures.
- [ ] Existing mini backup/report/Aster worker behavior remains unchanged.

### M4 — Recovery, integration and graduation

- [ ] Jason runs Doctor, opens service UIs and SSH directly from MacBook without
  Screen Sharing, AI, the mini or a shared filesystem.
- [ ] Test with mini unavailable through a safe client-side isolation method;
  no reboot of the only active administration path as an incidental test.
- [ ] Verify local toolkit/docs remain usable when Forgejo is unavailable.
- [ ] Restore bootstrap/config/docs from protected backup into an isolated test
  location and demonstrate rebuild; preserve credential custody boundaries.
- [ ] Complete applicable integration updates and record accepted limitations.
- [ ] Focused milestone commits; permitted Forgejo pushes and read-only GitHub
  mirror verification, or explicit pending synchronization status.

## 10. Validation and evaluation

Test the real human workflow on the MacBook, including normal shell startup,
known-host verification, unavailable service/timeouts, denied target/action,
missing dependency, dirty repo and duplicate-install cases. Use synthetic config
fixtures for bootstrap conflict/rollback tests. Do not trigger production backup
or alert sends merely to test read-only diagnostic parity. Use the existing
baseline to separate migration failures from unrelated lab incidents.

A full model curriculum rerun is not applicable unless implementation changes an
Aster consumer; run targeted affected tests if it does. Avoid destructive failure
simulation and do not delete/revoke the mini’s working access for the independence
test. Obtain meaningful proof rather than relying on successful installation.

## 11. Observability and maintenance

Jason owns patches, tool manifests and key revocation. Mini remains the scheduled
report owner; MacBook checks are on demand with separate counters and no duplicate
notifications. Record toolkit version and check coverage per host. Detect obsolete
profiles or unavailable evidence visibly; do not require the mini to diagnose a
MacBook bootstrap problem. Changes to Doctor must preserve concurrent user edits.

## 12. Backup, restore and rollback

Git covers accepted source, not all untracked configuration or credentials.
Verify existing backup coverage on each Mac; no assumption that the mini’s
restricted private-export pull protects the whole administration environment.
Back up non-secret bootstrap manifests and unique local configuration through
an approved encrypted/versioned path. Keep passwords/keys in their approved
protected recovery mechanism, not ordinary Git bundles.

Rollback restores saved MacBook config, disables new launch/profile entries and
removes only the newly introduced public-key entries when authorized. Preserve
pre-existing access and user files. A lost MacBook is revoked independently; no
mini key rotation is required solely because the MacBook key is revoked. Test
restore in an isolated location before claiming two recoverable hubs.

## 13. Integration impact checklist

| Integration | Required change or disposition |
|---|---|
| HomeLab Doctor | MacBook profile, independent state and accurate production/host-local evidence |
| Monitoring/alerts | Mini-only ownership; no new continuous MacBook monitoring required |
| Backup/recovery | Per-host configuration coverage, isolated restore and independent recovery docs |
| NetBox | Reconcile MacBook/mini device/service facts only where adopted schema applies |
| Human wiki | Direct MacBook usage, bootstrap and lost-device recovery |
| Aster mirror | Publish accepted salient knowledge through existing derivation; resolve absent local path |
| Operational reference | Host roles, dependencies, paths, supported checks and identity labels |
| Repository docs | Portfolio/changelog now; operations/authorization/backups after implementation |
| Diagrams/rack | Workstation relationship only; no new rack, storage or power hardware |
| Homepage | No new service; validate existing dashboard directly from MacBook |
| Authentication | Unique MacBook SSH identity, existing human sign-in, scoped diagnostic capability manifest |
| DNS/certificates/firewall | No changes planned; read-only investigation of connectivity if needed |
| Automation/schedules | Existing mini remains executor; no MacBook production scheduling |
| Security inventory | Custody identifiers, revocation/rotation, permissions and cleanup ownership |
| AI administration | No new AI service granted access by this human-workstation project; any later addition must pass charter integration gate |

## 14. Graduation criteria

All applicable gates pass, repeated direct operation and recovery are proven,
documentation agrees with live state, access remains least privilege and neither
Mac requires the other for ordinary administration. Explain shared network/service
failure domains. Record exceptions with reason, owner and review point; unchecked
gates are not complete. Production remote synchronization remains explicit.

## 15. Evidence log

2026-09-24: reviewed charter, retired Standards pointer, master-plan ethos,
portfolio, backup and remote-administration records. Read-only storage assessment
and path/dependency discovery completed. No secret contents inspected. Jason
chose internal SSDs and removed external workspace migration from the project.
Drafted this MacBook-only Stream A plan; implementation has not started.

## 16. Resume instructions

Read charter and this project; inspect Git status and preserve unrelated work.
At discovery `.claude/settings.json`, `scripts/doctor.sh` and
`docs/projects/TrueNAS-DIY-SAS-Expansion.md` were already modified. Do not overwrite
or include them in project commits. Next implementation step is M0 acceptance
and direct MacBook discovery. Do not copy `~/.ssh`, install duplicate LaunchAgents,
move mini files or touch the attached external SSD.

## 17. Close-out

Proposed, not graduated. Current deliverable is the project document and portfolio
entry. No external storage change, new key, MacBook installation or remote write
was performed. Local project commit/synchronization status is reported separately.
