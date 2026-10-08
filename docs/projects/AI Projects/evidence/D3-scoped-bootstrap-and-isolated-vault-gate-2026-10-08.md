# D3 scoped bootstrap candidate and isolated vault experiment

## Attempt 2 result; narrower candidate for attempt 3

Jason approved corrected-path bundle `b0ce977...766b8d5`. Exact hash, source path
permissions, unit syntax and effective isolation/limits were checked. This time
the disposable engine started. Fixed metadata reported `passed:false`,
`failed_stage:provision`. Reaching that stage proves the preceding fixture
bootstrap, root revocation and eight 403-denial assertions passed. No successful
credential provisioning, admin self-revocation or complete handoff is claimed.
All fixture state disappeared with the owned server process; it never used real
credentials. Unit/file cleanup and independent absence checks passed; production
2.6.4 remains unsealed and local Doctor reports healthy (0 active, 37 outcomes).

Version-pinned source investigation:
[OpenBao 2.6.4 ACL evaluator](https://github.com/openbao/openbao/blob/v2.6.4/vault/policy/acl.go#L502)
applies required-parameter checks to ReadOperation before allowing empty request
data. Candidate read preflights supplied none. This is a source-backed explanation
for the provisioning failure; attempt 2 did not capture the exact failing request.
The next candidate records allowlisted provisioning stage names on failure.

Rather than adding unusual read payloads or weakening constraints, candidate 3
removes ALL policy/role write authority from the temporary provisioning token.
Human-only bootstrap now checks every new object's absence, creates the fixed
introspection policy and fixed role, verifies them, creates its narrow temporary
policy/token, then revokes root before delivery. Ordinary provisioning reads and
validates fixed configuration; it only writes two exact new KV records and issues
the bounded SecretID. Existing policy/role stage labels now mean read verification,
not configuration writes. No production bootstrap has occurred.

202 local tests pass, including no policy/role writes by provisioning and rejection
of weaker pre-existing configuration before credential writes. Previously approved
fixtures are not retroactively claimed to test these changes.

**New approval requested:** ONE attempt of the same isolated, memory-only,
private-network fixture on LXC 117, same unit/path, resource limits and cleanup as
attempt 2. Only reviewed candidate source/manifest contents change. It still uses
fictional credentials and never contacts production OpenBao. New archive:
`/private/tmp/aster-provision-isolated-v3-20261008.tar`, SHA-256
`533bd75bbf64361f2a19cc0a599f0c4326dd1c1d822d2d7236611ae628d780ca`.
Repeat the eight negative checks against the smaller permission set and require
successful ordinary provisioning plus admin revocation. Stop/clean up on failure;
no automatic retry or isolation relaxation. This gate supersedes earlier bundle
hashes. Earlier attempt approvals are consumed. No real ceremony is authorized.

## Attempt 1 result and corrected-path approval gate

Jason approved the original exact bundle. Staging and manifest verification
passed. `systemd-analyze verify` passed; effective unit properties confirmed
DynamicUser, PrivateNetwork/PrivateTmp, filesystem protections, empty capabilities,
resource limits and 120-second lifetime before start.

The unit failed with exit status 2 before the Python runner started:
PrivateTmp replaces `/var/tmp`, hiding the staged program. Therefore no disposable
vault, bootstrap API or permission tests ran. This is a packaging failure, not
evidence for or against OpenBao authorization behavior. No retry performed.

Stopped the fixture, verified exact unit content, removed all eight enumerated
files and staging directories, cleared only its failed state, reloaded systemd.
Independent check reports MainPID=0 and unit not found. Production vault remains
2.6.4 unsealed; corrected local Doctor passes (0 active requests, 37 outcomes).
The original approval is consumed.

Corrected candidate changes ONLY ExecStart/source staging to
`/opt/aster-provision-isolated-20261008`, outside PrivateTmp. The path was verified
absent. All isolation settings, tests, limits, unit name and cleanup requirements
remain as specified below. `/opt/openbao` stays inaccessible; the separate sibling
source directory is read-only under ProtectSystem=strict.

Request approval for ONE corrected attempt with the same bounded scope, replacing
the original source directory with the new `/opt` path. Before startup verify
the program is present, readable by the dynamic-user class (0644), ancestors
traversable, and not under a masked path. Do not disable PrivateTmp. Use new
archive `/private/tmp/aster-provision-isolated-v2-20261008.tar`, SHA-256
`b0ce977ca6df8b4644ed921e1d37a298d23a7726f04858fbd0306c074766b8d5`.
Eight files; only the unit and generated manifest differ from attempt 1.
No real credential, root ceremony, production restart or model call is included.

The historical original gate below is preserved for provenance; the corrected
path/hash above govern any newly approved attempt.

## Local preparation completed

`admin_contract.py` describes one dedicated ten-minute, non-renewable, orphan
service token without root/default/identity policies. Named-path authority covers
only the new introspection policy/role, two new credential records, SecretID
issuance and self lookup/revoke. Policy and role writes additionally require
all reviewed parameters and constrain their allowed values. No wildcard path,
other token creation, general secret listing or delete permission is granted.
KV v2 payload constraints are not claimed: custody writes remain bounded to two
exact paths and the provisioning helper uses CAS=0. This is not a universal
no-overwrite guarantee against arbitrary use of the temporary token.

`admin_bootstrap.py` is a candidate human-terminal helper. It accepts only a
newly generated, dedicated root token through a hidden prompt after exact local
fingerprint confirmation. It creates a new policy only after verified absence,
issues the restricted child, checks its metadata, revokes root, then delivers
the child to a fresh root-only runtime file. No root/recovery material reaches
the Mac controller. The ordinary vault node rejects broader or unbounded tokens.
No helper has run with real credentials or been installed remotely.

Handled failures attempt revocation; ambiguous revocation is not retried and no
success is claimed. Abrupt process/host death can interrupt root cleanup: the
fresh root token does not acquire a ten-minute limit merely because its child
has one. A private human recovery path must remain open until root revocation
is confirmed. The bootstrap policy remains a named object for reconciliation;
it is not automatically removed. Existing objects are never overwritten/reused.

200 local delegation tests pass, including expanded-authority rejection,
collision handling, root-before-child delivery ordering, failed delivery child
revocation and no retry after uncertain root revocation. These use fictional
APIs and are not proof of installed OpenBao enforcement.

## Why an isolated real-engine test is needed

The earlier approved rehearsal exercised mocked API behavior inside installed
Python runtimes. This experiment instead runs the installed OpenBao 2.6.4 engine
against empty in-memory storage and checks actual token/ACL semantics. Hypothesis:
the bootstrap token can complete the exact provisioning workflow while unrelated
reads, policy expansion, root-token creation and weaker role parameters get 403.
Parameter constraints can interact with reads/defaults; any unexpected denial or
allowance rejects this candidate rather than modifying production to fit it.

Primary sources consulted:
- [Token API](https://openbao.org/docs/api/auth/token/): token lifetime, orphan
  semantics and self-revocation. Current page labels 2.7.x; installed 2.6.4 must
  therefore be tested, not assumed identical.
- [Policy constraints](https://openbao.org/docs/concepts/policies/): explicit
  required fields and value restrictions; KV v2 does not support those payload
  constraints.
- [Root generation](https://openbao.org/docs/api/system/generate-root/): legacy
  unauthenticated ceremony is deprecated; retain existing authenticated human
  ceremony. Do not enable legacy endpoints or weaken listener controls.
- Installed `bao server -help`: dev storage is memory-only and
  `-dev-no-store-token` suppresses token-helper persistence.

## Exact approval requested — one disposable real-engine experiment

Target only existing OpenBao LXC 117. Do not restart its production service.

1. Recheck 2.6.4 unsealed health and absence of staging/unit names.
2. Copy the reviewed eight-file source/manifest archive to new root-owned
   `/var/tmp/aster-provision-isolated-20261008` (0755 directories, 0644 files;
   source only, no secret contents). Verify archive and every manifest hash.
3. Install only reviewed `deploy/aster-provision-isolated.service` as
   `/run/systemd/system/aster-provision-isolated.service`, verify its syntax and
   effective properties, reload systemd and run it once. Do not enable it.
4. The unit uses DynamicUser, PrivateNetwork, PrivateTmp, read-only system,
   protected home/devices, no capabilities, and explicitly inaccessible vault
   config/data/handoff paths. CPU capped at 50%, memory 512 MiB, swap zero,
   lifetime 120 seconds; kill the whole control group on stop. If isolation is
   unsupported, abort; do not remove isolation settings to make it work.
5. The runner starts only an owned `/usr/bin/bao server -dev` subprocess at
   127.0.0.1:38200 inside the PRIVATE network namespace. HTTP is confined to this
   empty fictional environment; production TLS is unchanged. It uses a clearly
   fictional root value, suppresses server output, never stores a token helper,
   and submits only fictional credential values. No access to real recovery
   files, credentials, production API, Authentik or Keychain is needed.
6. Validate bootstrap root revocation, eight negative authority cases, exact
   provisioning and scoped-token revocation. Emit only fixed result/failed-stage
   metadata. Any failure rejects this candidate; no in-place weakening/retry.
7. Stop the fixture unit if necessary; verify its processes are gone, remove
   only its unit and enumerated staging files, reload systemd, then confirm the
   production vault remains unsealed/healthy and broker readiness is unchanged.

Archive `/private/tmp/aster-provision-isolated-20261008.tar` SHA-256:
`10490dcf777665a381a20204b5034b76b8cbba13c3a92c6687f958627fc1ffa9`.
30,720 bytes, eight files including manifest. Sources: bootstrap, contract, vault
provisioner, isolated runner, two introspection configs and fixture unit.
Read-only preflight: systemd 257, installed OpenBao 2.6.4 healthy; staging/unit
paths absent. Source/scope changes invalidate this gate's fingerprint.

Risk: bounded resource contention on LXC 117; sandbox compatibility may fail.
Rollback: stop only the isolated unit and remove its files. In-memory fixture
state disappears on process exit. No new production backup is needed because no
production state/config is modified. Retain existing maintenance checkpoints.

Approval is required under repository AGENTS.md for the temporary remote unit,
files and process. No production provisioning, root ceremony, real credentials,
authority expansion, gateway activation, push or model call is authorized by
this experiment. After a successful test, complete cross-host private handoff
and the human ceremony instructions before the real provisioning gate.
