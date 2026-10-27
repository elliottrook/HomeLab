# Full-Aster first-screen transaction — inactive install card

Status: **APPROVAL-READY INACTIVE INSTALL / LIVE EFFECT EXCLUDED**

Source implementation: `codex/f4-f5-root-writer` at full commit
`b6dc186eef865924294b4e5cb1ef72d73c149733`. The exact eleven-file inventory
is `FULL-ASTER-FIRST-SCREEN-INACTIVE-INSTALL-MANIFEST-20261026.tsv`.

This installation makes the two-request Qwen3.6-35B full-Aster first-screen
transaction available but inert. It creates no unit or timer and does not run
the wrapper. It does not acquire a lease, produce F2-F5 evidence, change the
staged model, mount it into LXC110, stop or restart a guest/service, call a
model, change a schedule, or grant live authority.

## Measured target boundary

Read-only inspection on October 26 found the seven transaction modules, host
wrapper and LXC110 request helper absent. The two F4/F5 modules are the only
replacements: both are root-owned, one-link mode 0644 and match their accepted
predecessor hashes `db4066d0...` and `d57e95c1...`. The whole-host lease is
exactly `ready`.

The installed full-drain dependencies match source and custody: session
`104d6bdf...`, sources `233459b8...`, validator `88ab9828...`, cooperative
adapter `720a2c9a...`, deadline guardian `98149f2f...`, and runtime
`52e4b71e...`. The installed F2/F3/F4/F5 dependencies also match the fixed
source pins recorded in the earlier F4/F5 installation card. Any drift is a
stop condition.

## Inactive installation

1. Recheck source commit and every manifest hash. Recheck the lease is ready,
   transaction state/guardian/admission/F4/F5 effect targets are absent, and
   no full-drain lock or operation lock exists.
2. Preserve the two replaced files in a new root-only rollback directory,
   recording their exact hashes, modes and ownership. Stop if either
   predecessor differs from the measured values above.
3. Install the ten Proxmox files and one LXC110 helper through temporary files;
   publish new paths without replacement and replace only the two named F4/F5
   targets. Set root:root and the manifest modes. Do not create or reload a
   systemd unit.
4. Run `sh -n` on the wrapper. Run target-Linux imports with bytecode disabled,
   then the focused first-screen, F4/F5 and full-inference test suites from a
   clean source archive. Invoke the wrapper only without `--effect-authorized`;
   require the exact disabled response and no state or model request.
5. Recheck all eleven installed hashes/custody, unchanged dependency pins,
   ready lease, absent state/locks/evidence, disabled Stream A evaluation
   timers, and healthy LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL,
   Speech, News timers, `pvescheduler` and `pvestatd`.

## Rollback

On a failed install/import/test/postcheck, remove only new files that still
match this manifest and restore only the two checkpointed F4/F5 predecessors.
Recheck their exact former hashes and every production postcondition. Retain
all files and stop for reconciliation on changed bytes, unexpected state,
lease/lock creation, service transition or schedule drift.

A successful inactive installation does not authorize the live first-screen
transaction. That later effect requires a fresh F2-F5 chain, a separately
approved exact run card, a 45-minute bounded recovery window, and an LXC110
restart. The independent guardian must be armed first. The live transaction
is limited to two sequential synthetic requests and restores the accepted
9B/SYCL baseline, model custody, mount configuration, consumers and lease on
every accepted exit.
