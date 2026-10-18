# Combined supervised full-inference pilot — disabled-install card

Status: source-only candidate. This card does not authorize staging, service
stops, model starts, workload execution, reboot, GPU rebinding, or a remote
push. It supersedes the earlier phased-only candidate for any future pilot
review; that earlier approval must not be reused for this packet.

## Frozen source

The source tip is `73b17c92`. The host packet contains exactly nineteen files
under `/usr/local/libexec/local-ai-lease/full-inference-pilot/`; the in-guest
wrapper is a separately located candidate for LXC110, and its test is evidence
only. Every staged file must match these SHA-256 values before any future
installation review.

### Host packet

| File | SHA-256 |
|---|---|
| `application_b60_lease.py` | `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d` |
| `cooperative_lab_host_adapter.py` | `720a2c9ac9fb278223e31c998fe58af234d84451344daa63dabcf55b2ebd98a6` |
| `cooperative_lab_session.py` | `1a1c1f11219c0ec4a89671b7acb552e40d005a8e7fe056b8eab8225cc374e260` |
| `full_inference_lab_install_preflight.py` | `5a8586c9e6002ba6ce1a479a2b8fd1de3085e463d171abc11189c2b0ceb81f05` |
| `full_inference_lab_runtime.py` | `7509608d75025e49eeae7c304ee00fe451fd5f07f48b6916efef0d5d38a0a03a` |
| `full_inference_lab_session.py` | `104d6bdfa2296abfe026d0017ab935ca2351519fab84116b073e11afb3c6301d` |
| `full_inference_lab_sources.py` | `1f53e61b6909c26b6658d17396eff9babb4f2253b470fe33d8b188bfc9980c39` |
| `full_inference_lab_supervisor.py` | `7ee567a16040213ca3e8e0157019108074a06746fd15c8d38f91a943364a8684` |
| `full_inference_lab_validator.py` | `5cf1562a98c7a01528c5e3f2e2d80c69c5805f0e9dc4fceec1916d15d0d686f4` |
| `full_inference_lab_workload.py` | `84ef607d3e87a39c01d95010ab041b6fb2c4212b55d2f8f7d9fdd7719f8b49f6` |
| `host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `test_cooperative_lab_host_adapter.py` | `e9433ab5b35dc11881f0a5416e5c8cd94243919b5b7264e9ccf629bffbf73b7a` |
| `test_full_inference_lab_install_preflight.py` | `698b1699a48766dcda0aa470b08851ddf3f0c462f19edd0bb0d70f36cdabe2fa` |
| `test_full_inference_lab_runtime.py` | `bc0969f4429cf01eab61ae5854b267c73f73fef1ed2ad6605a7110fc8375c916` |
| `test_full_inference_lab_session.py` | `8d2d07119dd12f0f6c61a4cf4f7d679a445f60f8959170b759a78c7666470624` |
| `test_full_inference_lab_sources.py` | `eab6fb2fc1bc7aa0dd14ee001aee7a58bafb73faf5b3c0f0adb52b31e5be8650` |
| `test_full_inference_lab_supervisor.py` | `b8c2f503fa7ada32b17c7dbeeca8530f0c219922435eb77b50a8531b34612909` |
| `test_full_inference_lab_validator.py` | `b3806c9e769dbcf77efe23d616147365961087c91e7cd6413e3e7cb8c6341f91` |
| `test_full_inference_lab_workload.py` | `62384032c59ab97b90122de244ce4105768bac3011593dbdfaea4a62da7e4240` |

### LXC110 wrapper candidate

The wrapper candidate is not placed in the host packet. A separately approved
future staging operation would place it at
`/usr/local/sbin/aster-llama-lab-smoke` in LXC110, root-owned and mode 0750:

| File | SHA-256 |
|---|---|
| `aster_llama_lab_smoke_wrapper.py` | `0d131232c847fafbe5b04f3ac42664efe31eea003c37052c22a8c02a2b57e99d` |

Its evidence-only test is `test_aster_llama_lab_smoke_wrapper.py`, hash
`904b83de3841e6a911a05faba712cb50fd262cfa5222e3425d2334f82d3e4141`.

## Single bounded pilot entrypoint

The only combined pilot entrypoint is the default-deny runtime phase:

```text
PYTHONPATH=/usr/local/libexec/local-ai-lease/full-inference-pilot \
/usr/bin/python3 -B /usr/local/libexec/local-ai-lease/full-inference-pilot/full_inference_lab_runtime.py \
  --phase pilot --owner-id <owner> --admin-path-evidence <attestation> \
  --cycle <YYYY_MM_DD> --session-start-epoch <epoch> \
  --model-sha256 <sha256> --binary-sha256 <sha256> --unit-sha256 <sha256> \
  --effect-authorized
```

Without `--effect-authorized`, it returns `effects=not-attempted` and performs
no probes or effects. With the flag, the bounded path is still subject to a
separately approved live run and performs, in one owner-held process:

1. local-Proxmox source preflight and accepted baseline validation;
2. a render-node holder snapshot and fixed five-consumer drain;
3. the fixed three-request accepted-9B smoke on loopback port 11436;
4. heartbeats and a monotonic deadline bounded by the 30-minute lab window;
5. independent lab scope/listener/process/GPU absence proof; and
6. exact validator-backed restoration, retaining the lock on uncertainty.

The pilot claim is limited to known-consumer isolation, controlled smoke, and
restoration. Point-in-time occupancy snapshots are not a continuous deny-new-
GPU-opens boundary and do not claim host-wide B60 exclusivity. The pilot uses
the host's bounded `/proc` render-node descriptor observer. A
probe error is not interpreted as absence. The wrapper treats an already-gone
`--collect` systemd scope as harmless only when the independent absence proof
passes; unexpected stop failures remain errors. A pre-existing holder is
accepted only when it is the fixed production `llama-server` in the LXC110
cgroup, and the post-drain allowed-holder set is empty; a same-binary holder
outside that identity is rejected.

## Disabled verification and rollback

Before any staging review, run the import preflight and all synthetic tests
from a clean copy of this exact manifest. Confirm that no systemd unit, timer,
lease state, journal, backend process, model request, workload, network rule,
or guest state was created. The preflight must report the ten host modules,
five drain effects, eleven restore effects, and `effects=not-attempted`.

Rollback removes only this candidate packet and wrapper checkpoint. It must not
stop or start a guest, alter schedules, alter GPU binding, touch VM105, or
execute the accepted-9B control. Any uncertain state retains the lock for
manual reconciliation.

This card does not close TrueNAS mirror, F2 archive integrity, F3 retained
receipt, MacBook custody, or host-wide GPU exclusivity gates. Those remain
separate promotion requirements.
