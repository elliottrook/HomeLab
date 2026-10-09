# D3 scoped bootstrap candidate and isolated vault experiment

## Attempt 5 — PASS; isolated vault-side experiment complete

Jason approved v5 `4da4c90...52a89ca9`. Exact archive/per-file hashes, absent paths,
unit syntax, source permissions and effective isolation/resource limits checked.
Installed OpenBao 2.6.4 in the private-network memory-only fixture reported:

```json
{"passed":true,"version":"2.6.4","negative_checks":8,"root_revoked":true,"admin_revoked":true,"real_credentials_used":false,"production_vault_contacted":false,"model_calls":0}
```

This confirms bootstrap created/verified the exact fixed configuration, revoked
its fictional root before scoped-token delivery, denied all eight out-of-scope
actions, completed the two fictional credential records and SecretID issuance,
then revoked the scoped administrator token and verified denial afterwards.
The successful run used about 1.067 seconds CPU and 66.2 MiB peak memory according
to systemd. The success result is from real engine APIs, not mocked responses.

Stopped the fixture after completion, verified its exact file inventory/unit
content and removed only all eight staged files, directories and runtime unit.
Reloaded systemd. Independent checks: unit not found/MainPID 0; staging absent.
Production remains 2.6.4 initialized/unsealed; Aster/broker/approval active;
corrected local Doctor healthy with 0 active requests and 37 historical outcomes.
No production root ceremony, accounts, policies, credentials, model calls, service
restarts, delegation activation or push occurred. Approval consumed.

Do not repeat this successful primitive without a new reason. Prior four failed
attempts remain evidence of bugs and diagnostic limitations in the candidate.
206 local tests remain the last full-suite result; no source edits in attempt 5.

Remaining scope: cross-host owned-pipe integration and complete private human
ceremony/staging/crash-reconciliation procedure before real inactive provisioning.
This isolated test does not prove those paths, actual Keychain/gateway delivery
in combination, live application authorization, token expiry under interruption,
or general sysadmin authority. Delegation remains disabled.

## Attempt 4 diagnostic result; exact-network comparison candidate

Approved v4 hash matched; isolation and source visibility verified. Fixture
bootstrap confirmed all five names absent, created/read the fixed policy and
created/read the role successfully. The only reported role mismatch was
`token_bound_cidrs`. Fresh fictional root self-revocation returned 204 after
rejection. No ordinary provisioning or child delivery occurred. The fixture
unit/files were removed and independently absent; production vault remains
2.6.4 unsealed and AI-PAM readiness healthy (0 active requests, 37 outcomes).

Source explanation: [version-pinned tokenutil](https://github.com/openbao/openbao/blob/v2.6.4/sdk/helper/tokenutil/tokenutil.go)
serializes bound CIDRs using SockAddrMarshaler. Upstream
[marshal implementation](https://github.com/hashicorp/go-sockaddr/blob/master/sockaddr.go)
calls String(), and [IPv4 formatting](https://github.com/hashicorp/go-sockaddr/blob/master/ipv4addr.go)
omits /32 for a host address. Dependency links are upstream master, not a pinned
dependency revision. The live diagnostic did not print values: canonical host
formatting is the source-backed explanation, to be tested in the next attempt.

Candidate v5 compares only `token_bound_cidrs` as strict parsed networks rather
than literal strings, with exact list cardinality and network-set equality.
It accepts a host with or without /32, rejects broader subnets, other/additional
hosts, malformed values, numeric coercion and ports. All other fields retain
existing checks. Diagnostic comparison shares the same helper. Policy, role
request, privileges and isolation remain unchanged. 206 local tests pass.

**Next approval:** one same-scope isolated v5 run, maximum 120 seconds, mandatory
cleanup, no real credentials or production changes. Eight-file archive
`/private/tmp/aster-provision-isolated-v5-20261008.tar`, SHA-256
`4da4c90a06c64e2a9a45a763bd7caca6f735a9eec5d4ef0bd469bc4052a89ca9`.
Only comparison code/diagnostic reuse and manifest change. No previous approval
authorizes this repeat. Preserve all failed attempts; no successful full workflow
is claimed until the real-engine test completes.

## Attempt 3 result; diagnostic-only candidate for attempt 4

Jason approved v3 `533bd75...8d780ca`. Hash, preflight health, staging, unit syntax,
source visibility and all effective isolation properties passed. The runner
reported `passed:false, failed_stage:bootstrap`; exit status 1. It did not reach
the negative tests or credential provisioning. Exact cause remains UNKNOWN:
the prior report omitted API status and failed validation fields. Do not infer
that policy enforcement or scoped-token creation passed from this attempt.

Stopped the unit, verified exact unit/file inventory and removed all approved
staging files/unit. Cleared only its failed state and reloaded systemd. Independent
checks confirm unit not found/MainPID 0 and staging absent. Production 2.6.4 remains
unsealed; local Doctor is healthy with 0 active requests and 37 recorded outcomes.
No real credentials, production vault API changes, model calls or pushes.

Prepared v4 changes ONLY the fixture runner's diagnostic reporting: allowlisted
method/path/status metadata for bootstrap/provision calls and known field NAMES
when fixed role verification fails. Never prints response bodies, field values,
tokens or exception details. Two regression tests verify filtering; full local
suite now 204 passing. Authority, bootstrap logic, unit, limits and isolation
are unchanged. This is an information-gathering attempt, not an asserted fix.

**Approval requested:** one isolated diagnostic run, same eight-file scope,
`/opt/aster-provision-isolated-20261008`, same temporary unit, 120-second cap and
mandatory cleanup/production validation. Do not retry or change permissions on
failure. New archive `/private/tmp/aster-provision-isolated-v4-20261008.tar`, SHA-256
`d69e166db4296a7dbb4424174ba25280fc7284cea94c5769256054e8e53e76b8`.
Only runner/manifest differ from v3. All previous approvals consumed; no private
human ceremony or real provisioning is authorized. Once diagnostics identify the
failure, resolve it locally before proposing further execution.

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
