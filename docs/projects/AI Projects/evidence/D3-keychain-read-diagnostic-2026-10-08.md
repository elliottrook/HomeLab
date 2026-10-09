# D3 — private Mac credential-read diagnostic

Status: APPROVED DIAGNOSTIC COMPLETE — KEYCHAIN READ TIMEOUT. Approval consumed.

## Supervised read — approved and completed

Jason approved the 90-second supervised invocation. It completed once with
`readable_valid_shape` in 24.69 seconds, credentials printed false, network calls
zero and model calls zero. The source fingerprint matched the prepared helper.
No account activation, gateway restart, ACL change, OAuth request or unattended
read was performed. Approval consumed; the earlier timeout remains valid evidence.

This proves supervised readability and accepted text shape, not correctness at the
token endpoint or unattended availability. The elapsed time includes waiting for
the human/OS interaction; it is not a Keychain performance benchmark. Do not
simply extend every production credential-read timeout or claim Always Allow is
required. Current WorkerToken reads Keychain for each gateway request; that is
unsuitable for this supervised path. Next local design work should consider one
explicit supervised session bootstrap, a short-lived in-memory worker token for
the bounded assignment, online gateway revocation checks on every request, and
no automatic credential reacquisition on expiry. No such implementation or live
pilot is authorized by this diagnostic alone.

### Approved scope retained

Jason dismissed the stale prompt and requested continuation. Prepared a separate
explicit `--supervised` mode in the same helper. This allows 90 seconds for a
human response; it does not change the production worker's five-second timeout.
Three local fixture tests pass. No real credential read occurred during this
preparation. Existing five-second results below retain their original fingerprint.

Request approval for exactly one invocation:

```text
python -B services/aster-agent/delegation/diagnostics/keychain_read.py --run --supervised --approved-sha256 6109b2e4b9680c46c9a9765f6745397283bab05db341205e2fc8841bf2773111
```

Use the existing private test interpreter on the Mac. Read only the same fixed
item through the same private pipe and `/usr/bin/security`, with no network,
activation, model call, service restart or Keychain configuration change. Report
only the existing fixed result category and elapsed seconds. No automatic retry.
Use short tool polling intervals so the user can receive updates while waiting.

When the fresh prompt names `Aster worker Authentik credential`, Jason enters his
login Keychain password into macOS only and selects **Allow** once. Do not select
Always Allow, change ACLs, unlock via command-line password arguments or send the
password to this chat. If denied/timed out, stop and report. Success proves only
supervised private readability, not unattended operation or complete OAuth access.

This fresh real-credential read requires specific approval under the repository
credential-access boundary; no additional permission expansion is requested.

## Result

Jason approved the exact helper. Ran it once with the pinned source fingerprint.
It reported `keychain_read_timeout`, elapsed 5.01 seconds, no credential output,
zero network calls and zero model calls. The timed-out subprocess was terminated
by Python's subprocess timeout handling. No account activation, token issuance,
gateway restart, Keychain modification or permission change was performed.

This reproduces failure at the private Keychain-read stage under the worker's
five-second limit. It does not establish that the item/password is invalid,
that a longer timeout will fix it, or that the rest of authentication works.
Earlier metadata lookup succeeded without requesting the password; that is a
different access operation. The original provisioner used a 15-second limit and
reported a successful private read during setup; do not silently substitute that
timeout or repeat credential access based on correlation alone.

Source inspection confirms the installer configured `/usr/bin/security` as the
explicit reader, rather than allowing every application. This is repository
implementation evidence, not a fresh inspection of the live item ACL. Whether
macOS is waiting for an access/unlock prompt or another operation is unresolved.
Asked Jason whether a prompt appeared, without requesting its password or values.
Next safe action: use that observation to choose a focused diagnostic or fix;
keep delegation disabled and do not repeat the pilot or recovery ceremony.

The original approved diagnostic specification is retained below.

### Human observation

Jason supplied a screenshot of the macOS dialog: `security` wants access to
`Aster worker Authentik credential` and requests the login Keychain password,
with Always Allow, Deny and Allow choices. This establishes that an access prompt
appeared during the failed read; it does not establish the underlying ACL/lock
condition or unattended readability. The diagnostic process had already timed
out. Advised dismissing that stale request with Deny. A fresh, separately
authorized supervised read can allow time for Jason to enter his password only
in the OS dialog and choose Allow once. No Always Allow/ACL change, password
disclosure, model execution or service restart is authorized by this observation.
Do not describe this interactive path as a production unattended credential path.

The corrected pilot reached a healthy gateway but stopped at its credential check.
Aster is restored, the worker is inactive, zero provider grants exist and no job
or model call occurred. See the [retry result](D3-authenticated-pilot-retry-2026-10-08.md).

## Exact diagnostic

Run only `services/aster-agent/delegation/diagnostics/keychain_read.py` once with
`--run --approved-sha256` matching:

`7fc4c09a34f68c177e69e5d237117cc8a609774b8451ff746efe31e920ce800b`.

It reproduces only the existing worker's fixed `/usr/bin/security` read of service
`com.elliottrook.aster-codex-worker`, account `authentik-app-password`, using the
same five-second timeout, stdin disabled, private stdout pipe, discarded stderr
and minimal PATH environment. It requests no other Keychain entry. The returned
value stays in the local process, is checked only for the worker's expected text
shape, and is not printed, written, hashed, sent to a model or used on the network.
Python memory is not claimed to be cryptographically erased.

Only one fixed status category and elapsed seconds are reported: readable valid
shape, readable invalid shape, timeout, denied/failed, invalid encoding, or other
failure. The exception text, password, length and private output are excluded.
Two local fixture tests passed, including secret-bearing simulated errors.
Default execution reports disabled; exact source-hash approval is required.

This does not activate the user, issue tokens, contact Aster, restart a service,
change Keychain permissions, renew/rotate credentials, admit a job, run a model,
or push Git. If macOS requests access, this is only the exact named entry; no
Keychain-wide access or security-setting change is authorized. Stop on failure;
no automatic retry. There are no retained objects to roll back.

The result will distinguish the local password-read stage from later token
exchange without another production deployment. If this succeeds, the original
failure remains unresolved and a separate sanitized stage-aware proposal is
needed; success must not be relabelled as proof of the complete credential path.

Approval is needed because this deliberately reads a real credential inside a
private helper after the previous one-shot credential check was consumed.
Repository read-only discovery excludes credential values. Jason need not paste
or upload any value or perform another OpenBao recovery ceremony.
