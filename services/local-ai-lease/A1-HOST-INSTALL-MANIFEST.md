# A1 host installation manifest

Status: offline candidate only. No file in this manifest has been installed
by this checkout.

## Exact source/dependency copy set

The A1 result is explicitly a **stream-a-candidate-path-baseline** measurement,
not a measurement of the deployed LXC104 Aster. The candidate is pinned to
commit `e6b638e4`; its complete local import closure is recorded in
`A1-Aster-source-bundle-inventory-2026-10-14.md`. The platform owner must copy
that closure and exactly the guarded Stream A1 files below. The inventory is
resolvable in the Stream A handoff worktree at
`docs/projects/AI Projects/benchmarks/A1-Aster-source-bundle-inventory-2026-10-14.md`
(latest inventory commit `a9606829`, superseding `2610e908`):

| Candidate baseline item | SHA-256 |
|---|---|
| `aster_agent.py` | `d6a05bcc7edddb1eaa69a67450cfc48c1c0e96ba8688de7a1246a1e9eb847e11` |
| `requirements.txt` | `a1beddbeac7ac0afc27f3659b41defe0af9f5dcbf9fb91516cd86d9f4ace2929` |

The inventory lists the complete local import closure. Before installation,
the platform owner must additionally prove the exact installed dependency
versions and wheel hashes. A missing closure member, dependency mismatch or
deployed-source substitution aborts the run.

The candidate requirements pin FastAPI 0.133.1, httpx 0.28.1, Pydantic 2.13.4,
Uvicorn 0.41.0, PyJWT 2.14.0 and pywebpush 2.5.0. The requirements-file hash
is pinned above; wheel hashes are not yet known and must be captured by the
source-local installer without exposing credentials.

The reviewed Stream A source is pinned to worktree commit `e6b638e4` for the
guarded gateway/factory files below; those files must be paired only with the
pinned candidate Aster closure. The platform owner must copy exactly these
files and verify the hashes before enabling the disabled unit:

| Destination under `/opt/aster-a1-test` | Source at pinned commit | SHA-256 |
|---|---|---|
| `a1_isolated_app.py` | `scripts/aster-adaptive/a1_isolated_app.py` | `cf8d88506d19acdcfd53caa88804dd6f780e94412b7c0a2e3f779a59241b2a5d` |
| `a1_test_gateway.py` | `scripts/aster-adaptive/a1_test_gateway.py` | `5350e9f293caa19cf2f993016a56dfdee5e2ccfc2f049eecaa55044bd1786e07` |
| `aster_asgi_clock.py` | `scripts/aster-adaptive/aster_asgi_clock.py` | `e7f8240fc38a62772ac2d7e4e9461ee8f3be21580885d9dfc0cab40fe1919305` |
| `a1_headless_client.py` | `scripts/aster-adaptive/a1_headless_client.py` | `beabc81ad44d205bc908c248f2fea50fb12faaac01f654a160712a550aa3fbc2` |
| `a1_service_runner.py` | `services/local-ai-lease/a1_service_runner.py` | `feae2ec1f423ec4cbcde33112a64ed6db0963a6c3868726bcdff732b07b520c1` |
| `a1_key_file.py` | `scripts/local-ai/a1_key_file.py` | `018340fe0bf8a7ec7526d2d0709d21cc8f11fcef6c252cdbfeb6798cc6a055cd` |
| `a1_ingress_policy.py` | `scripts/local-ai/a1_ingress_policy.py` | `faef14be94817c846cf1f6bb8bc618adf49ac31485237087b53566a77be618ed` |
| `aster-llama-ingress-apply` | `services/local-ai-lease/aster-llama-ingress-apply` | `41b96f560261a198c09fd85d8ba7150478241fbe6a38f28befad9dc4fa40020b` |
| `aster-llama-ingress-restore` | `services/local-ai-lease/aster-llama-ingress-restore` | `9bf3c3cb1e04081f41584f9dc742d86e9e7ead3a1806a243a6ce3478572ff347` |
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
It is not a lease receipt. The host controller persists an armed state with
start-by and restore deadlines before it stops only the two allowlisted
consumers; only after that state exists may the
platform receipt producer emit the real source-bound application lease receipt.
The sidecar and final A1 batch are blocked until that receipt validates.
The admitted final process has no second inner listener. Wrong-inner-key
behavior is exercised only by a disposable misconfigured factory/app fixture
or inner FastAPI auth check; it is never produced by mutating the admitted
final process. The live admitted-path proof is header stripping and replacement
with the configured inner test key.

Before each key or ingress effect, persist an effect-intent transition in the
armed lease state; after the host observer confirms the effect, persist the
matching observed transition. A crash with no intent skips that effect during
recovery. A crash after intent but before observation is uncertain and must
retain the lease rather than replay blindly.

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

The ingress helpers are additive and handle-bound: they accept only the
observed empty `inet filter input` baseline, add one tagged drop rule for
non-`192.168.70.10` sources to TCP 11435, and restore by deleting only that
tagged handle. They never replace a complete nftables ruleset. Their focused
parser tests are in `scripts/local-ai/test_a1_ingress_policy.py`.

