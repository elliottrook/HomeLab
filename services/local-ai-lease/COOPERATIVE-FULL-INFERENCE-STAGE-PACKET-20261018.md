# Full-inference drain no-effect staging packet

Status: prepared commands only. Do not run the transfer, target writes or
service probes until the disabled-stage approval is separately recorded. The
packet is pinned to source commit `a6cbbec8`; the recurring supervisor design
is not part of this 14-file candidate.

## Build and verify locally

From the repository root, create a temporary bundle containing exactly the
fourteen files in the disabled-install card:

```sh
stage=$(mktemp -d /tmp/full-inference-drain-stage.XXXXXX)
for f in \
  full_inference_lab_session.py test_full_inference_lab_session.py \
  cooperative_lab_session.py cooperative_lab_host_adapter.py \
  test_cooperative_lab_host_adapter.py full_inference_lab_sources.py \
  full_inference_lab_validator.py full_inference_lab_runtime.py \
  full_inference_lab_install_preflight.py test_full_inference_lab_sources.py \
  test_full_inference_lab_validator.py test_full_inference_lab_install_preflight.py \
  application_b60_lease.py host_exclusion.py; do
  git show a6cbbec8:scripts/local-ai/$f > "$stage/$f" || exit 1
done
shasum -a 256 "$stage"/*.py | sort > "$stage/SHA256SUMS"
cd "$stage"
shasum -a 256 -c <<'EOF'
104d6bdfa2296abfe026d0017ab935ca2351519fab84116b073e11afb3c6301d  full_inference_lab_session.py
8d2d07119dd12f0f6c61a4cf4f7d679a445f60f8959170b759a78c7666470624  test_full_inference_lab_session.py
1a1c1f11219c0ec4a89671b7acb552e40d005a8e7fe056b8eab8225cc374e260  cooperative_lab_session.py
720a2c9ac9fb278223e31c998fe58af234d84451344daa63dabcf55b2ebd98a6  cooperative_lab_host_adapter.py
e9433ab5b35dc11881f0a5416e5c8cd94243919b5b7264e9ccf629bffbf73b7a  test_cooperative_lab_host_adapter.py
1f53e61b6909c26b6658d17396eff9babb4f2253b470fe33d8b188bfc9980c39  full_inference_lab_sources.py
5cf1562a98c7a01528c5e3f2e2d80c69c5805f0e9dc4fceec1916d15d0d686f4  full_inference_lab_validator.py
1a9898dde72399f435ed93f88322be53675dd2ac49a0aeb20495a9781ad80848  full_inference_lab_runtime.py
7f725f00bf3aa62bfac7697575e5b5735a5186e915e98cddac0ebfe5adca1e06  full_inference_lab_install_preflight.py
eab6fb2fc1bc7aa0dd14ee001aee7a58bafb73faf5b3c0f0adb52b31e5be8650  test_full_inference_lab_sources.py
b3806c9e769dbcf77efe23d616147365961087c91e7cd6413e3e7cb8c6341f91  test_full_inference_lab_validator.py
fc5425aff28517ab5e29cfd562bb4af01dbd7be620022ef928fc123be1da7a1d  test_full_inference_lab_install_preflight.py
deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d  application_b60_lease.py
f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563  host_exclusion.py
EOF
```

The final `sha256sum --check` must be run from `$stage`; any mismatch stops.

## Proposed transfer and target no-effect check

The following is a command template only. It is intentionally not executed
in this turn:

```sh
scp -q -o BatchMode=yes -o StrictHostKeyChecking=yes \
  "$stage"/*.py proxmox:/tmp/full-inference-drain-stage/
```

After separate approval, the target operator must verify the transfer before
any install write, then run only the following read-only baseline commands:

```sh
sha256sum /usr/local/sbin/local-ai-lease
stat -c '%U:%G %a %n' /usr/local/libexec/local-ai-lease /usr/local/libexec/local-ai-lease/full-inference-drain
ss -ltnp | grep ':11435' || true
systemctl is-active aster-llama.service aster-speech.service aster-agent.service
systemctl is-enabled news-aggregator-ingest.timer news-aggregator-digest.timer
qm status 105
readlink /sys/bus/pci/devices/0000:04:00.0/driver
```

The target install preflight is then run from a private temporary directory
with only the fourteen transferred modules on `PYTHONPATH`:

```sh
PYTHONPATH=/tmp/full-inference-drain-stage /usr/bin/python3 -B -c \
  'from full_inference_lab_install_preflight import validate_imports; print(validate_imports())'
PYTHONPATH=/tmp/full-inference-drain-stage /usr/bin/python3 -B -m unittest \
  test_full_inference_lab_session test_cooperative_lab_host_adapter \
  test_full_inference_lab_sources test_full_inference_lab_validator \
  test_full_inference_lab_install_preflight
```

Expected output includes `effects: not-attempted`, five drain effects and
eleven restore effects. These checks must not create the target directory,
systemd units, lease state, journal, model request, process, timer, network
rule or workload.

Repeat the read-only baseline commands and compare them to the saved before
snapshot. Any listener, unit, schedule, GPU binding, VM105 or lease-state
delta is a failed staging result.

## Rollback

If only the temporary transfer directory exists, remove that directory. If a
future approved stage copied the candidate into the concrete target directory,
remove only those fourteen candidate files and restore the separately captured
prior bytes, ownership and modes. Do not stop/start services, alter schedules,
touch VM105 or GPU binding, invoke the runtime entrypoint, or run the queued
accepted-9B control as part of rollback. If target state is uncertain, retain
the evidence and stop for operator reconciliation.

This packet does not solve the continuous-exclusion gap. The live run remains
NO-GO until the persistent supervisor or a reviewed legacy-controller block
exists.
