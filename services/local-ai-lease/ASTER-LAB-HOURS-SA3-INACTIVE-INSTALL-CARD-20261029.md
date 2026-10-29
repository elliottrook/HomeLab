# SA3 Lab Hours — dormant Proxmox/LXC110 installation card

Status: **source-only candidate; installation and activation are not authorized**

Packet: `ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json`
Packet SHA-256: `9173ea4179f16efcd635ca9eefe5d9f767b07dfee082e250f0a1a22a898b7a0c`

This redesign follows the read-only Proxmox preflight. It does not upgrade the
working Lab Hours core. The live CLI, reservations, runner, manifest, guardian
and runtime remain untouched; the live runner is preserved at its observed
`6ba44c2bfb6322d68c5bd6c112e4144916be60f2ee4ae0abf2042e09a456abd2` / `0755`
baseline. SA3 registration and `WORKLOAD_RUNNER_UNAVAILABLE` remain a later,
separate effect gate.

## Exact dormant target set

On Proxmox, install only these two root-owned `0644` dormant modules under
`/usr/local/libexec/local-ai-lease/full-inference-pilot/`:

| File | SHA-256 |
|---|---|
| `sa3_expanded_quality_transaction.py` | `0706912279bcb4a511633cfb22f19e691eed94f4aa79e07bdc332f87d0dbbc70` |
| `sa3_listener_adapter.py` | `a6387092f04a8fa8cc35254ce19c9a479cd0177b2fd53caae40ee6012c38f917` |

No manifest, CLI, reservation store, runner, guardian, runtime, unit or timer
is an installation target. The compatibility check imports only these dormant
modules against the clean target path and therefore does not require newer
core APIs.

In LXC110, install exactly four root-owned `0644` runtime files under
`/usr/local/libexec/local-ai-lease/full-inference-pilot/`, plus the wrapper as
root-owned `/usr/local/sbin/aster-llama-lab-sa3` mode `0750`:

- `sa3-expanded-source-quality-v1.json` — `ed75836af74401709a74333a96d0a22629b23e389e5262bbc365ab6aed018d23`;
- `sa3_expanded_quality_packet.py` — `b9011bef592421b6e6c28ec830b17f1296409daa30fd4f508d913ba35c104657`;
- `sa3_expanded_quality_runner.py` — `39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351`;
- `sa3_fair_scorer.py` — `92a4526886b21492995b73c834844a570b7718415abcadce848bcd1da6860bda`;
- wrapper — `27949ff1ba37f825de8d3c4aaeaf6388b9535e72d0063e46eac0e491a6604303`.

Answer keys and independent-review material must be absent. No SA3 service or
timer may exist in either target.

## Fixed bundle and transaction

The deterministic source bundle builder is
`scripts/local-ai/build_sa3_inactive_bundle.py`; it selects only the packet,
installer, two dormant host modules, four Stream A runtime files and one
wrapper source (the wrapper is copied to its two reviewed target locations).
It emits a deterministic archive, sidecar digest and generated bundle
manifest, rejects answer/review material, makes the packet `0600`, makes all
other source files `0644`, and removes its transient build stage by default.

The fixed installer is `scripts/local-ai/sa3_inactive_install.py`. Its default
mode is source-only; `--apply` is required for a separately authorized live
operation. It verifies the root-owned staged bundle, source hashes and custody,
the observed live runner baseline, target imports, excluded files and absent
units. It checkpoints every dormant target on Proxmox and LXC110, installs
atomically, and automatically rolls both sides back on host write, guest write,
postcheck, import or rollback uncertainty. Checkpoints and failure evidence
are retained when state is uncertain.

For a future separately authorized operation, the exact preparation boundary is:

```text
python3 -B scripts/local-ai/build_sa3_inactive_bundle.py \
  --output-dir /var/lib/local-ai-lab/bundles/sa3-inactive-install-8dc6eac5
sha256sum -c /var/lib/local-ai-lab/bundles/sa3-inactive-install-8dc6eac5/aster-sa3-inactive-install-8dc6eac5.tar.gz.sha256
install -d -o root -g root -m 0700 /var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5
tar --no-same-owner --no-same-permissions --no-overwrite-dir \
  -xzf /var/lib/local-ai-lab/bundles/sa3-inactive-install-8dc6eac5/aster-sa3-inactive-install-8dc6eac5.tar.gz \
  -C /var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5
chown -R root:root /var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5
chmod 0700 /var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5
chmod 0600 /var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5/services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5/scripts/local-ai/sa3_inactive_install.py \
  --stage-root /var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5 --apply
```

These commands are documentation only and were not run. The archive, sidecar
and checkpoints are retained through the authorized postcheck/rollback window;
the extracted transient stage is removed only after successful reconciliation.

## Validation and exclusions

The clean temporary-PYTHONPATH compatibility proof imports the dormant host
modules, the guest runner and wrapper without bytecode or network access. The
bundle proof verifies exact selection, source commits, hashes, modes, root-only
stage custody, packet `0600`, source `0644`, archive retention and exclusion of
all answer/review files. The combined focused suite passes **60/60**.

Recorded source hashes for this candidate are:

```text
c84f99878b731cd9a710372baf829e3ee37383c485526827a47247ba32ba2a37  scripts/local-ai/sa3_inactive_install.py
b52341f76f822308ccb0375b17f836709a67edb2e1e9937e41a7f0864aa203f1  scripts/local-ai/build_sa3_inactive_bundle.py
f4c36bd6a5a904a855aa0e4d5c6644ba475e42dc670b71f6a2fed97aed45670f  scripts/local-ai/test_sa3_inactive_install.py
dca7b42d06fbde9de45c159a33089d22cd41342afb94e3037c04f5b9e3e9d44f  scripts/local-ai/test_sa3_inactive_install_packet.py
33d1b19bd61a8899aaa5bb0817779ab256b28a86d05e28e5446bc106332f508e  scripts/local-ai/test_build_sa3_inactive_bundle.py
```

This lane performs no booking or Lab Hours window check, lease acquisition,
production drain, model/GPU/backend/routing change, service/timer change,
restart/reboot, credential change or remote push.
