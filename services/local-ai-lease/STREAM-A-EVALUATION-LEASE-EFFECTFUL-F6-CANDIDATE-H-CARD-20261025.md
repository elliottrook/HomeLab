# Stream A candidate-H plus M3 effectful F6 card

Status: **SOURCE-ONLY FUTURE RUN CARD; HOLD**

This card supersedes candidate-G effect cards. It is not authority to create
evidence, arm recovery, acquire a lease, stop consumers, start either workload,
call a model, restore services or push Git.

## Frozen installed packet

The live operator may not select paths or substitute files. Recheck these
installed identities before producing any effect intent:

| Installed path | SHA-256 |
|---|---|
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | `3d6e976b5fcb33a5645ec35fd0fe337ebbb57600edbbd03fe074b165e440a4d7` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | `2d4ff31f75dc98af9f745ca7e24310ac3627b9b36e8a29bf9a50f8debb0911f0` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | `d3c8924e4e1cb5165d70ca36a4fc335b465445d1881390a8ba7c83ab44a508ed` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_admission.py` | `3e54f54239df4ceeeb9dfdf9166fdbd7b9bb9bb9bbd3d5119c17f1092480b686` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_watchdog.py` | `19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_watchdog.py` | `c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner.py` | `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner_heartbeat.py` | `4c45a07098eb8cca31bf95bb50b0824b65c6772e636627b23219761f359ed6cc` |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restore_observer.py` | `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3` |
| `/usr/local/libexec/local-ai-lease/trusted_observer.py` | `6091b5572764abf3675d9140e760083a1482fee8abfef8fc763fb72853618f5f` |
| `/usr/local/sbin/stream-a-evaluation-lease` | `15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af` |
| `/usr/local/sbin/stream-a-evaluation-owner` | `4d4e848eeafffdfa3aa9a0ba84097d94487318235442b1a4e4b8edc04a043014` |
| `/usr/local/sbin/stream-a-evaluation-owner-heartbeat` | `e0162f60983601192c5f0fdd6d8395604e6636c05c9653c643d3722872dce12a` |
| `/usr/local/sbin/stream-a-evaluation-watchdog` | `65012c196134242a76a2131fbc9d7f28b50bcfd9137a87cfda0a416345430c99` |
| `/usr/local/sbin/stream-a-evaluation-restore-observe` | `5cb6bec83864b5a8eeeb1b8c0624b93498fc04b2fcf36afb61e13caa0e64e8ab` |

The five fixed systemd files are
`/etc/systemd/system/stream-a-evaluation-owner.service`,
`stream-a-evaluation-owner-heartbeat.service`,
`stream-a-evaluation-owner-heartbeat.timer`,
`stream-a-evaluation-watchdog.service` and
`stream-a-evaluation-watchdog.timer`, with respective SHA-256 values
`640c753b…2371`, `6c777750…2ad5`, `a5840b5b…3192`, `02ff7c4a…d932` and
`7b2170f6…9811`. All packet files are root-owned, one-link regular files with
the reviewed `0644` or `0755` mode.

Candidate-H is fixed to LXC104 launcher
`/usr/local/libexec/aster-d4-candidate-h-launcher` at `71c07060…0eb`, unit
`/etc/systemd/system/aster-d4-candidate-h.service` at `76c0ba89…2450`, run
digest `423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4`
and output directory `/var/lib/aster/d4-candidate-h-output`. M3 is fixed to
LXC110 runner
`/var/lib/aster-nlu-calibration/nlu-calibration-v1/nlu_calibration_runner.py`
at `b8ada869…e11` and manifest
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
The F4/F5 and recovery authentication boundary additionally fixes LXC110
`/usr/local/libexec/aster-a1/llama_auth_probe.py` at
`93e78f8a9c40bb9808ac71c5215404c8f10b3e5116383095d196281293682582`.
It must require no-auth `401`, fixed-invalid-bearer `401`, then real-key `200`
with the exact accepted model, using GET-only metadata and no inference body.

## Fixed runtime paths and identities

- lease ID: generated once as `stream-a-evaluation-<cycle>-<16 lowercase hex>`;
- generation: literal `1`;
- owner ID: `stream-a-evaluation-owner-<same 16 lowercase hex>`;
- state: `/var/lib/local-ai-lab/stream-a-evaluation/lease.json`;
- lease and operation locks: sibling `lease.lock` and
  `lease.operation.lock`;
- owner intent and heartbeat: sibling `owner-intent.json` and
  `owner-heartbeat.json`;
- watchdog identity: `/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json`;
- watchdog status and restore intent: sibling `watchdog-status.json` and
  `restore-intent.json`;
- F5 and admission: sibling `f5-observation.json` and `admission.json`;
- effect intents: `/var/lib/local-ai-lab/stream-a-evaluation/intents/`, a new
  root-owned mode-`0700` directory containing fixed-name root-owned mode-`0600`
  JSON files for each phase;
- rollback checkpoint: `/var/lib/local-ai-lab/checkpoints/stream-a-evaluation-live-<cycle>-<same 16 lowercase hex>`,
  root-owned mode `0700` and created before arming.

All dynamic epochs and evidence digests must be emitted by one reviewed
orchestrator from the independently accepted cycle evidence. They are never
typed or selected by the operator. `hard_deadline_epoch` is the run start plus
4,500 seconds; `restore_deadline_epoch` is the run start plus 5,400 seconds;
heartbeat timeout is 45 seconds. A later source revision must provide that
orchestrator and its rollback before this card can become approval-ready.

## Exact arm and phase interface

After the checkpoint and root-owned `owner-intent.json` exist, the only arm
operation is enabling and starting these two timers:

```text
systemctl enable --now stream-a-evaluation-owner-heartbeat.timer
systemctl enable --now stream-a-evaluation-watchdog.timer
```

The timer dependency starts the fixed owner service; the operator must not
manually start it because the unit has `RefuseManualStart=yes`. Continue only
after the fixed identity and a matching unexpired heartbeat exist and both
timers are enabled and active.

Independent platform review confirmed this dependency order is structurally
sound: the heartbeat timer invokes the heartbeat service, whose `Requires=`
edge dependency-starts the owner service; the matching-heartbeat gate prevents
progress before that owner has written its exact identity. The watchdog timer
is then armed before acquisition and remains inert until durable lease state
exists.

Every lease phase has this command shape, with the phase and fixed intent file
selected by the orchestrator:

```text
/usr/local/sbin/stream-a-evaluation-lease --phase <fixed-phase> \
  --intent /var/lib/local-ai-lab/stream-a-evaluation/intents/<fixed-name>.json \
  --effect-authorized
```

The serial phases are `acquire`, `quiesce`, `post-quiescence`, D4 `start`, D4
`outcome`, M3 `start`, M3 `outcome`, then `restore`. The exact acquire object
has the entrypoint's 20 fields, including empty `quiesced_targets`, the fixed
four-consumer baseline, exact model/backend/endpoint and the canonical
`admission_receipt`. Post-quiescence embeds those same acquire bytes and the
exact stopped-state observation. Start uses only the fixed workload name;
outcome binds the fixed packet digest, journal/result digests, call count,
elapsed seconds, `tool_free=true` and `transport_uncertain=false`. Restore
binds the captured baseline, accepted backend/auth/idle observation, sole GPU
holder and explicit recovery boolean. Any schema, digest or state mismatch is
fail-closed.

The actual workload commands, surrounded by their corresponding start/outcome
phases, are fixed as:

```text
pct exec 104 -- systemctl start aster-d4-candidate-h.service

pct exec 110 -- sh -c 'cd /var/lib/aster-nlu-calibration/nlu-calibration-v1 && exec timeout --signal=TERM --kill-after=10s 1230s /usr/bin/python3 nlu_calibration_runner.py --source cases.json --release release.json --development nlu-development-v1.json --output run.json --journal attempt-journal.jsonl --key-file /etc/aster-llama-api-keys'
```

The first command may run once only. The second is admitted only after an
accepted candidate-H outcome and sufficient restoration reserve. Neither is
an operator-editable shell template.

Recovery uses only the installed watchdog callback through
`/usr/local/sbin/stream-a-evaluation-restore-observe` and the fixed restore
phase. Cleanup disables the two timers, stops the owner after restored state
is proven, removes current identity/intent files only after their retained
copies are hashed into the checkpoint, and independently compares all four
consumer states, accepted backend/GPU/auth state, News schedule, F2 schedule,
lease/operation locks and evaluation child processes with the checkpoint.
Uncertain cleanup retains state and locks for reconciliation.

## Serial admission boundary

An effectful run can be considered only after all of these are complete and
independently reread for one cycle:

1. current-cycle backup chain and successful three-row F2 result;
2. retained F3 archive-integrity receipt;
3. fresh F4 pre-acquire receipt bound to the proposed lease ID and generation;
4. fresh content-free F5 observation covering the LXC110 mirror, exact schedule
   set, accepted model/binary/unit/auth identities, four-consumer baseline and
   absence of conflicting work;
5. canonical admission artifact binding the exact bytes and digests of F2,
   F3, F4 and F5, candidate-H and M3;
6. active independent watchdog and owner heartbeat with a tested constrained
   restore path; and
7. a separate exact approval for the live 90-minute outage and run.

Missing, stale, future-dated, cross-cycle, foreign-lease, changed, weakly
custodied or ambiguous evidence is NO-GO. No phase infers success from clock
time or a filename.

## Exact bounded run

The entrypoint first persists `PREPARED` with the admission digest, then masks
and stops only the registered Aster Agent, Speech and two News timers while
retaining the accepted `aster-llama.service`. Post-quiescence must prove the
same admission bytes, exact stopped set, authenticated idle endpoint and sole
accepted GPU holder before entering `RUNNING`.

The first and only D4 attempt is:

`systemctl start aster-d4-candidate-h.service` in LXC104.

It is accepted only when the static installed service and launcher identities
match, the run digest is
`423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4`,
the private journal/result pass their structural review, the outcome is bound
to the lease/generation, transport is certain and the restoration reserve is
intact. There is no automatic retry.

Only an accepted candidate-H outcome admits the one M3 NLU calibration run,
pinned to manifest
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
M3 cannot start first, repeat, use tools, or borrow the final 15-minute restore
reserve.

## Recovery and terminal proof

Any admission drift, heartbeat loss, deadline, command uncertainty, rejected
outcome or observer failure enters recovery. The adapter restores the captured
four-consumer baseline and proves accepted llama.cpp/SYCL health,
authentication and idle exclusive GPU custody. Lease and lock release occurs
only after that proof. Uncertain recovery retains durable state, locks,
admission and workload evidence for manual reconciliation.

Completion requires candidate-H then M3 terminal outcomes, exact restoration,
healthy production consumers, accepted backend identity, no evaluation child,
and no residual lease or lock. It does not promote a model, enable automatic
routing, or change the D3 manual-Codex HOLD.
