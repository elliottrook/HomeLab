# SA3 candidate-i inactive install result — PASS — 2026-11-04

The fresh corrected archive was deterministic twice at
`ccf1b1e6dd96f0ac96578bae54bacd19543990a87eb129c0cac49efb5e03865a`
and bound platform commit `bd20d29db4105868b12f3839913028d10d21810f`
plus Stream A commit
`f94116365aeb9b18cdabe29ce3acbb37d07d6734`.

The inactive installation passed after rechecking the exact predecessor bytes,
root custody, executable modes, absent target/checkpoint/units, ready lease and
absent shared state/locks. It replaced four host files, added two host modules,
verified one existing guest dependency and added five candidate-i guest files.
Independent rereads matched every expected hash:

- workload registry:
  `829024378e11ec98ff67dc42d1554588f68b4e95f8115532081e29663e87ab70`;
- reserved runner:
  `eab869dae32340d302c25c6346843b94c6d79a539eccf975cfe9d7c69ca47960`;
- full runtime:
  `6c7767e5a22829d3369b5c385495aea7d2879986c9adb5e698aef29d3df198ad`;
- release manifest:
  `c2812b754c2d5c87156898548d63a407f5afcca7ac7d4000ece645b14a922a5e`;
- host transaction / adapter:
  `c1d40abe685860ba6202ea5b18425a1ba8fbcc5e5aa7e820ae555ec08c922131` /
  `e16a251225ca0cc757c74cd3b38641700aeabf9f32391836309ebfe42fd0a8c6`;
- guest packet / deterministic v1 / deterministic v2 / batch v2 / runner v2 /
  wrapper:
  `0b9bfb86…625d0` / `9f8b14f8…e3da3` /
  `4ca154c6…1943` / `eaeddb10…70d4e` /
  `58b932a6…9188c` / `a3db03b8…9a74`.

Both host and guest checkpoints are root:root mode 0700 and retained. Host
imports, the 36-pin release manifest, registered runner identity, guest
diagnosis-only parser and packet binding passed. LXC104/110/116, Aster Agent,
accepted 9B/SYCL, Speech, pvescheduler and pvestatd remained healthy. Lab Hours
dispatcher and Doctor timers are active/waiting and their last service results
are success/0. There is no candidate-i process or scope, booking, unit, lease
state or shared lock. Temporary target staging was removed.

No model request, quality packet execution, service restart, route, repair
authority or promotion occurred. Candidate-i is installed inactive. The next
gate is a new exact ledger-clear Lab Hours booking with normal live
lease/lock/health preflight.
