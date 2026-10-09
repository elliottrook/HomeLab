# D3 — private Mac credential-read diagnostic

Status: PREPARED; NOT APPROVED OR EXECUTED.

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
