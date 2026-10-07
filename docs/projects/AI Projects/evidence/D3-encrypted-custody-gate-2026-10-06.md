# D3 encrypted custody check — approval gate

Jason confirmed Recovery A and a second independent recovery key are available.
This confirms availability only: it is not authorization to access recovery
material or change the vault. No keys were requested or accessed.

## Completed local preparation

- `vault_provision.py`: exact-policy/role/two-secret setup candidate, fingerprint
  gated, rejects existing/unverifiable objects, uses KV create-only CAS, verifies
  source-local secret round trips, records write intent before sending and refuses
  automatic retries/deletion on uncertainty. Its transport/delivery callbacks are
  still supplied by a future reviewed controller; no CLI mutation path exists.
  Policy/role APIs have no create-only CAS here: provisioning requires an exclusive
  administrative window and collision checks, not a claimed atomic transaction.
- `credential_delivery.py`: source-local encrypted AppRole delivery through
  systemd-creds pipes; verifies decryption without a plaintext file, atomically
  publishes a new 0600 ciphertext file, refuses overwrite. Host-key encryption
  protects service-file custody, not against root or someone holding the host
  key and ciphertext. Python process memory is not claimed to be securely erased.
- Candidate systemd drop-in loads the encrypted credential; it does not enable
  delegation and has not been installed.
- **171 local delegation tests pass**. New tests cover vault collisions, lost
  writes, unconfirmed delivery, encrypted round-trip publication and no overwrite.
  Crypto tests use explicit doubles; they are not real host encryption evidence.

## Verified read-only host facts

LXC 104: systemd 257.13, `systemd-creds` supports host-key encryption and explicit
credential names. Aster is active as User/Group `aster`. LXC 117: OpenBao 2.6.3.
Metadata-only checks found the staging/fixture paths below absent and
`/var/lib/systemd/credential.secret` absent. No credential contents were read.

## Exact requested operation

On LXC 104 only:

1. Recheck paths and unit absence. Create root-owned 0700 staging directory
   `/var/tmp/aster-custody-tools-20261006`; stage only `credential_delivery.py`
   and `custody_host_check.py`, verify their combined fingerprint:
   `fbac03972fc66376bbda43b516cc138c802c2f4f604eec92a186b49a8c7a4b93`.
2. Run that exact check once as root. It creates the private fixture directory
   `/run/aster-worker-custody-check-20261006`, encrypts fixed fictional values,
   and checks the decrypt round trip. systemd will generate its previously absent
   root-only host encryption key as part of encryption. Do not print/copy that key.
3. Start one transient unit `aster-worker-custody-check-20261006` as user `aster`
   with only the fictional credential. Its Python probe checks exact fixture
   equality and emits only a fixed success marker. Verify ordinary Aster-UID
   access to the root-owned encrypted source is denied.
4. The completed transient unit is collected; the helper removes its fixture on
   success. Remove only the two staged files and their empty staging directory
   after retaining sanitized results. Independently verify the unit/fixture are
   absent and Aster/approval services remain active.

No vault/Authentik access, real credentials, recovery shares, model call, new
identity/group, service restart, permanent unit, delegation enablement or Git push.
The only intended persistent host change is the systemd host encryption key.
Existing LXC backup scope includes its location; no backup was run/tested by this
preflight. For later guest restore, reissue expired AppRole material rather than
assuming an old encrypted credential is valid. Do not delete the new host key
as casual rollback because other credentials could subsequently depend on it.

Failure/rollback: preserve the named fixture and sanitized stage evidence. Inspect
the exact transient unit before stopping/removing it if still active; remove only
this operation's fictional files after reconciliation. Do not restart Aster or
modify vault state as recovery. A failed check leaves delegation disabled.

Repository `AGENTS.md` requires explicit confirmation before these remote writes.
This gate is ready; it does not authorize later real provisioning. Once this
boundary is proven, finish the protected controller, Authentik policy/Keychain
provisioning and gateway mount before the human recovery ceremony is opened.

## Primary sources

Installed `systemd-creds --help` and [systemd v257 upstream documentation](https://raw.githubusercontent.com/systemd/systemd/v257/man/systemd-creds.xml)
confirm pipe I/O, name binding, automatic host-key creation and root-accessible
host-key protection. The public rendered manual returned HTTP 403; upstream source
was read instead. OpenBao API references for the candidate:
[KV v2](https://openbao.org/api-docs/secret/kv/kv-v2/),
[policies](https://openbao.org/api-docs/system/policies/) and
[AppRole](https://openbao.org/api-docs/auth/approle/). These pages did not render
usable API text in the browser tool; exact API behavior still needs bounded
deployment validation and is not established by merely linking them.
