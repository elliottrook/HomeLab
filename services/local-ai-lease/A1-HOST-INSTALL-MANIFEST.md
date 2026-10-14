# A1 host installation manifest

Status: offline candidate only. No file in this manifest has been installed
by this checkout.

## Exact source/dependency copy set

The Stream A source is pinned to worktree commit `72566b5f` until it is merged
into this branch. The platform owner must copy exactly these files and verify
the hashes before enabling the disabled unit:

| Destination under `/opt/aster-a1-test` | Source at pinned commit | SHA-256 |
|---|---|---|
| `a1_isolated_app.py` | `scripts/aster-adaptive/a1_isolated_app.py` | `cf8d88506d19acdcfd53caa88804dd6f780e94412b7c0a2e3f779a59241b2a5d` |
| `a1_test_gateway.py` | `scripts/aster-adaptive/a1_test_gateway.py` | `5350e9f293caa19cf2f993016a56dfdee5e2ccfc2f049eecaa55044bd1786e07` |
| `aster_asgi_clock.py` | `scripts/aster-adaptive/aster_asgi_clock.py` | `e7f8240fc38a62772ac2d7e4e9461ee8f3be21580885d9dfc0cab40fe1919305` |
| `a1_headless_client.py` | `scripts/aster-adaptive/a1_headless_client.py` | `92878a4642c5cf3895c3a4e76ddefe55d3a84526b163f431eb38192de470534a` |
| `a1_service_runner.py` | `services/local-ai-lease/a1_service_runner.py` | `feae2ec1f423ec4cbcde33112a64ed6db0963a6c3868726bcdff732b07b520c1` |
| `a1_key_file.py` | `scripts/local-ai/a1_key_file.py` | `018340fe0bf8a7ec7526d2d0709d21cc8f11fcef6c252cdbfeb6798cc6a055cd` |
| `aster-agent/` | exact reviewed Aster source/dependency bundle | host preflight required |

The Aster bundle must use the accepted source/dependency manifest and must not
include production environment files, OpenBao material, broker sockets,
knowledge, Doctor evidence or household state. The final deployment receipt
must include every copied file's digest; an unlisted file or digest mismatch
aborts before service start.

The final config must be owned by `aster-a1-test:aster-a1-test`, mode 0600, and
contain the final 20 frozen A1 request hashes. The disposable probe config must
be a separate file with a separate 20-hash fictional probe set, separate
journal, separate credentials and a separate digest. It must never contain a
final A1 request body. It is served by a separate disposable probe
gateway/configuration, never by the final admitted gateway.

## Disabled unit and identity

Install `aster-a1-test.service` disabled and verify:

```text
systemctl is-enabled aster-a1-test.service  -> disabled
systemctl is-active aster-a1-test.service   -> inactive
getent passwd aster-a1-test                 -> uid 1904, no supplementary groups
ss -ltn                                     -> no listener on 192.168.70.10:19104
```

Creation is reversible: record the pre-existing passwd/group database hashes,
create only `aster-a1-test` UID 1904 with no login shell/home, and on rollback
stop the unit, remove only its state/credential directories and remove that
UID only after `ps`, `ss` and open-file checks prove no process remains.

## Credential delivery

Generate ingress, inner and backend keys independently on the platform. Write
one root-owned mode-0600 `/etc/aster-a1-test/runtime.env` containing only the
test environment values, then use systemd `LoadCredential` to deliver it to
the UID. Compare SHA-256 digests locally; never print or export key values.
The backend key is also added as one new line to LXC110's existing
`/etc/aster-llama-api-keys` with an atomic create-once checkpoint. Preserve the
file's observed owner/group/mode exactly (`ollama:ollama`, 0600 on the current
host); do not assume root ownership. The existing production line is not read
into the operator session, changed or removed. Removal is hash-bound to the
immutable pre-add checkpoint and root-owned test-key digest file, refuses an
unknown or ambiguous match, and is idempotent after successful removal.

## Ingress and egress candidate

LXC104 is shared with production Aster, so a container-wide nftables allowlist
would also restrict production and is explicitly rejected. The disabled unit
uses per-service `IPAddressAllow`/`IPAddressDeny` as the candidate boundary:
loopback and `192.168.70.12/32` only. Before any model call, the platform
owner must discover exactly one named Mini client address and validate that
only it can reach port 19104 using a host/network ACL; do not substitute a
whole-subnet allow. If one client address cannot be pinned, abort.

The live observer must capture the packet-policy/counter state before and
after disposable attempts to a known listening Authentik/OpenBao endpoint, a
known listening non-backend LAN endpoint, and an Internet endpoint. Those
attempts must be denied while an authenticated request to
`192.168.70.12:11435` succeeds. A refusal from a non-listening service is not
network-denial evidence. If per-service counters cannot be observed without a
container-wide rule, abort rather than installing a broad nftables rule.

For the backend claim, checkpoint LXC110's existing ingress policy and apply a
temporary rule that admits only source `192.168.70.10` to TCP 11435. This
excludes Mac/LAN clients and other guests while the two production consumers
are quiesced. The receipt may set `exclusive_backend_claim=true` only after
policy read-back, an allowed sidecar backend request, and an excluded
listening-client denial are all observed. No-load or one-time connection
listings do not establish exclusivity. Before restoration, restore the policy
checkpoint and verify the normal production source set is admitted again;
retain the lease if that read-back is uncertain.

## Key-file update and rollback

1. Save a root-only checkpoint of `/etc/aster-llama-api-keys` without printing
   its contents.
2. Atomically write the original lines plus the new test line; preserve mode,
   owner and newline format.
3. Restart `aster-llama.service` once and verify the production key works, the
   new test key works, and a wrong key returns 401 on `/v1/chat/completions`.
4. On rollback, atomically restore the checkpoint, restart once, and repeat the
   production-key and wrong-key checks. Any uncertainty leaves the checkpoint
   and lease open for platform reconciliation.

## Preflight and receipt order

The pre-lease phase produces only a source-bound application backup checkpoint,
health/quiescence observations and a protected planned lease ID/generation.
It is not a lease receipt. The host controller persists leased state and stops
only the two allowlisted consumers; only after that state exists may the
platform receipt producer emit the real source-bound application lease receipt.
The sidecar and final A1 batch are blocked until that receipt validates.
The admitted final process has no second inner listener. Wrong-inner-key
behavior is exercised only by a disposable misconfigured factory/app fixture
or inner FastAPI auth check; it is never produced by mutating the admitted
final process. The live admitted-path proof is header stripping and replacement
with the configured inner test key.

## Application watchdog requirement

The whole-host recovery watchdog is not sufficient for this lease. The
application watchdog must own these fixed commands and checks: stop
`aster-a1-test.service`; restore the LXC110 ingress-policy checkpoint; remove
the test-key line from the key-file checkpoint; restart llama.cpp; verify the
production key succeeds and the wrong key is denied; then start Aster and
Speech. If any command or postcheck fails, retain the application lock/state
and do not start consumers. The offline command contract and recovery-order
tests are in `scripts/local-ai/application_b60_watchdog.py` and
`test_application_b60_watchdog.py`.

