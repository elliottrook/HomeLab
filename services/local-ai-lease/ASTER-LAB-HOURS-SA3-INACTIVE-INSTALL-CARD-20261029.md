# SA3 Lab Hours — dormant Proxmox/LXC110 installation card

Status: **source-only candidate; installation and activation are not authorized**

Packet: `ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json`
Packet SHA-256: `114186c44ec59a92768e04eb963a8a4e8d4705fa8b3eff6201913782f4af500a`

This redesign follows the read-only Proxmox preflight. It does not upgrade the
working Lab Hours core. The live CLI, reservations, runner, manifest, guardian
and runtime remain untouched; the live runner is preserved at its observed
`6ba44c2bfb6322d68c5bd6c112e4144916be60f2ee4ae0abf2042e09a456abd2` / `0755`
baseline. The preserved runner is pinned to
`6ba44c2bfb6322d68c5bd6c112e4144916be60f2ee4ae0abf2042e09a456abd2` / `0755`;
its observed unregistered-workload path contains `WORKLOAD_NOT_REGISTERED` and
does not contain the `sa3-expanded-source-quality-v1` identity. The live
manifest likewise does not register that identity. SA3 registration remains a
later, separate effect gate.

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
The archive digest is pinned to
`6e54c4dac9acf050061ed707638d921bfbb756bffd567b985fc2855f801ed709`; the
builder rejects any different output.

The fixed installer is `scripts/local-ai/sa3_inactive_install.py`. Its default
mode is source-only; `--apply` is required for a separately authorized live
operation. It verifies the root-owned staged bundle, source hashes and custody,
the observed live runner baseline, target imports, excluded files and absent
units. It checkpoints every dormant target on Proxmox and LXC110, installs
atomically, and automatically rolls both sides back on host write, guest write,
postcheck, import or rollback uncertainty. Checkpoints and failure evidence
are retained when state is uncertain.

For a future separately authorized operation, build in the reviewed local
checkout, then upload the exact archive and sidecar to a temporary Proxmox
path. Install them into the root-only incoming directory, verify the sidecar
with an explicit absolute-path comparison, and only then extract the fixed
0700 stage. Proxmox does not run the repository builder:

```text
BUNDLE_DIR="$(mktemp -d -t aster-sa3-bundle.XXXXXX)"
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/local-ai/build_sa3_inactive_bundle.py \
  --output-dir "$BUNDLE_DIR"
scp -q -o BatchMode=yes \
  "$BUNDLE_DIR/aster-sa3-inactive-install-8dc6eac5.tar.gz" \
  "$BUNDLE_DIR/aster-sa3-inactive-install-8dc6eac5.tar.gz.sha256" \
  proxmox:/tmp/
ssh -o BatchMode=yes proxmox 'set -eu
  incoming=/var/lib/local-ai-lab/incoming/sa3-inactive-install-8dc6eac5
  archive="$incoming/aster-sa3-inactive-install-8dc6eac5.tar.gz"
  sidecar="$archive.sha256"
  install -d -o root -g root -m 0700 "$incoming"
  install -o root -g root -m 0600 /tmp/aster-sa3-inactive-install-8dc6eac5.tar.gz "$archive"
  install -o root -g root -m 0600 /tmp/aster-sa3-inactive-install-8dc6eac5.tar.gz.sha256 "$sidecar"
  read expected_name expected_file < "$sidecar"
  test "$expected_file" = "aster-sa3-inactive-install-8dc6eac5.tar.gz"
  actual="$(sha256sum "$archive" | awk "{print \\$1}")"
  test "$actual" = "$expected_name"
  test "$actual" = "6e54c4dac9acf050061ed707638d921bfbb756bffd567b985fc2855f801ed709"
  stage=/var/lib/local-ai-lab/staging/sa3-inactive-install-8dc6eac5
  install -d -o root -g root -m 0700 "$stage"
  tar --no-same-owner --no-same-permissions --no-overwrite-dir -xzf "$archive" -C "$stage"
  chown -R root:root "$stage"
  chmod 0700 "$stage"
  chmod 0600 "$stage/services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json"'
rm -rf "$BUNDLE_DIR"
```

After the separately authorized staging boundary, the fixed transaction is:

```text
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
all answer/review files, and two independent builds have the same pinned
archive digest. The combined focused suite passes **61/61**.

Recorded source hashes for this candidate are:

```text
865be943c64e5de00f2e6ef8f55e4ed60d5a3b322faca949075d745ee4d2a317  scripts/local-ai/sa3_inactive_install.py
65e30c8e79e8bf81c8e23d1304255910198b036a44e33e9af51f3e52e4d196d9  scripts/local-ai/build_sa3_inactive_bundle.py
c513ceff67b1a45dae9576594a5905724b3c8ca00ecd8387a913986aa7014842  scripts/local-ai/test_sa3_inactive_install.py
13523d94c008ed49f3a37565058a8ad99451194814666ddd7ee734591db8755a  scripts/local-ai/test_sa3_inactive_install_packet.py
45c34d90f3eb438385cb279ea1dd20413760ded32b742ca77d0b152425901c50  scripts/local-ai/test_build_sa3_inactive_bundle.py
```

This lane performs no booking or Lab Hours window check, lease acquisition,
production drain, model/GPU/backend/routing change, service/timer change,
restart/reboot, credential change or remote push.
