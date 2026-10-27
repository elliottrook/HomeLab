# Full-Aster first-screen October 27 effect review

## Decision

**STATIC GO / LIVE EFFECT REQUIRES EXPLICIT RESTART APPROVAL.** Platform commit
`972c1d24` binds the already installed `b6dc186e` transaction to one October 27
invocation between 03:10 and 03:30 Vancouver. It permits no retry.

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

The source passed 22 first-screen, 11 F4/F5 and 62 full-inference target-Linux
tests at inactive installation. The card changes no model, persistent unit,
timer, schedule, routing, authority or tool grant. A live invocation still
needs Jason's exact approval because it restarts LXC110 and makes two model
requests. If any fresh gate fails, the outcome is NO-GO with no invocation and
no retry; the next action is to diagnose the first failed dependency rather
than silently schedule another cycle.
