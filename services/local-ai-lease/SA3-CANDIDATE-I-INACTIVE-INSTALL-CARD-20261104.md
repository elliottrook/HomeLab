# SA3 candidate-i inactive install card — 2026-11-04

This card freezes one reversible inactive installation. It replaces four
already-installed host files only from their exact candidate-g baseline, adds
two candidate-i host modules, validates the existing deterministic-v1 guest
dependency, and adds five candidate-i guest files. It preserves root-only host
and guest checkpoints and refuses any existing candidate-i timer/service,
lease/lock state, target collision, hash drift or uncertain rollback.

The deterministic bundle binds platform source plus Stream A commit
`f94116365aeb9b18cdabe29ce3acbb37d07d6734`. Target proof imports all host
modules, validates the 36-file release manifest and exact registered workload,
imports the guest wrapper/batch/runner, and proves the diagnosis-only known
metadata parser. The proof does not open or execute the untouched quality
packet.

Installation remains inactive: it creates no booking or unit, invokes no
model, stops/restarts no service and grants no route, repair authority or
promotion. After exact installation and postchecks, a separate ledger-clear
booking is still required for any candidate execution.
