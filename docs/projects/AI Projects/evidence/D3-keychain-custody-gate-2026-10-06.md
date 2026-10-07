# D3 Mac Keychain custody — exact approval gate

**Completed:** approved check passed; independent cleanup returned item not found.
See [result](D3-keychain-custody-result-2026-10-06.md). Approval is consumed.
The procedure below is retained as historical provenance.

**Prepared, not executed.** The gateway's encrypted delivery passed; this is the
remaining unverified storage primitive on the Mac. The private provisioning
controller must not assume that a compiled helper proves Keychain access works.

## Approved scope requested

Run `keychain_host_check.py` once on Jason's Mac, from the active worktree, with
the exact combined source fingerprint:
`2175c99afda3aefea71eef5dc9e3d4ee303e47e24831c9481b6eb6ff5d1ae159`.
This binds the check and `deploy/InstallWorkerCredential.swift`.

1. Query only service `com.elliottrook.aster-codex-worker`, account
   `authentik-app-password`. Stop unless Keychain explicitly reports item not found.
   Do not read or replace a pre-existing item.
2. Compile the existing helper into a disposable private temporary directory.
3. Create that one item using the intentionally public fictional value
   `aster-fictional-custody-check-20261006`, supplied through stdin only.
   The helper sets an explicit `/usr/bin/security` trusted-reader ACL, not an
   allow-all-applications ACL, and does not enable synchronization.
4. Read only that item with the exact worker reader. Compare privately and report
   booleans only. No real password, model or issuer is involved.
5. Only if the contents match the fictional fixture, delete the exact item and
   independently confirm not-found. Remove the temporary compiler output.

No human Companion/ChatGPT login item, default Keychain/search-list setting,
vault, recovery key, production identity, service or remote repository is changed.
Do not install or enable the worker. macOS may display a Keychain consent prompt;
do not bypass it, automate credential entry or broaden trust to complete the check.

## Failure and recovery

An existing item or ambiguous absence stops before mutation. Lost creation
acknowledgement, access denial or mismatch stops without automatic retry/deletion.
Retain the exact public fixture identifier for reconciliation. Cleanup may delete
only an item whose value is independently confirmed to match this fixture; never
delete by name alone after uncertainty. Keep delegation disabled on failure.

The check proves only this same-user reader path. It cannot establish isolation
from arbitrary code running as Jason or qualify a tool-enabled sysadmin worker.
Those limits from the [identity checkpoint](D3-identity-provisioning-2026-10-06.md)
remain. Legacy Keychain API warnings make host validation necessary before
committing to this custody implementation.

## Evidence and authorization

178 local delegation tests pass. Four new tests cover inert default, refusal when
an item exists/absence is ambiguous, exact fixture read/cleanup order and refusing
to delete mismatched contents. Default CLI invocation emitted the fingerprint
with `applied:false,keychain_accessed:false`. No Keychain query or write occurred.

The programme's D3 credential-path approval boundary applies to this new Keychain
item/ACL. Local code-edit permission is not silently treated as approval to change
the user's credential store. This exact gate requests that permission; it is not
approval for real credential provisioning or a model call.

Additional read-only preparation: installed OpenBao CLI help confirms the
authenticated root-generation workflow supports stdin shares and PGP/OTP
protection. The earlier project locates the human recovery bundle in
`Documents/OpenBao Recovery`; no Markdown/README/text guide was returned by the
name-only documentation search there. No bundle contents or keys were opened.
Keep the ceremony closed until the protected controller and human instructions
are complete. After this check, finish those and the single integration deployment;
do not repeat successful primitive checks without a new reason.
