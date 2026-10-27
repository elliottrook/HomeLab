# Full-Aster first-screen October 27 effect review

## Decision

**GO — SCHEDULED / CONDITIONAL AFTER ABSOLUTE-WINDOW CORRECTION.** Platform commit
`972c1d24` binds the already installed `b6dc186e` transaction to one October 27
invocation between 03:10 and 03:30 Vancouver. It permits no retry.

B60's published exact-peer characterization at `457ffa1a` prompted review of
the actual installed effect path. The public machine preflight it characterized
is non-authoritative and is not imported by the live controller. The installed
controller independently collects fixed F2/F3 bytes, produces F4/F5, binds the
generated lease and arms the guardian first. However, the launcher computes
both deadlines relative to actual process start and does not enforce the card's
absolute date/start window. A delayed start after 03:30 could therefore move
recovery beyond 04:15. That is a material mismatch with the approved effect.

Platform candidate `6dbdea2c` rejects every start outside October 27 03:10–03:30
America/Vancouver before any guardian, lease or effect, retains the 30-minute
effect limit, requires a real 15-minute recovery interval and caps hard recovery
at 04:15. Its focused launcher/controller/guardian suite passes 9/9. The
corrected launcher was subsequently approved and installed at exact SHA-256
`11568103c134b98821aad4154e79645375f15f3021fdaf9ce232340d8ef24d66`.
The rollback predecessor is root-only, the installed date/window contract
passed and the unchanged timer remains active for 03:10 PDT. Lease and effect
state remained clear and production stayed healthy with zero Aster/llama
restarts.

The card correctly requires an accepted three-row F2 result, independently
verified F3 receipt, completed 03:00 pull, exact installed/source/artifact
hashes, ready state-free lease, healthy baseline/consumers/schedules, no
competing work and enough time for the fixed recovery reserve. These are fresh
runtime gates and cannot be inferred from tonight's scheduled timers.

The effect is limited to the installed wrapper: independent guardian first,
fresh lease-bound F4/F5 and workload admission, registered-consumer drain,
temporary unprivileged artifact mapping, two LXC110 stop/start transitions,
one transient reasoning-on 35B unit and exactly two synthetic requests. The
30-minute owner deadline and 15-minute recovery reserve are inside Jason's
accepted 90-minute outage budget. Every accepted exit restores the fixed mount,
root artifact custody, accepted 9B/SYCL/auth baseline, consumers and lease.

The original source passed 22 first-screen, 11 F4/F5 and 62 full-inference target-Linux
tests at inactive installation. The card changes no model, persistent unit,
timer, schedule, routing, authority or tool grant. A live invocation still
has Jason's effect approval because it restarts LXC110 and makes two model
requests; Jason separately accepted the corrected launcher hash. Fresh runtime
gates still control the invocation. Any failure remains NO-GO without retry.
