# M3 K2 development transaction result — 2026-11-06

## Outcome

Reservation `aster-stream-a-m3-k2-20261106-2000-r1` is terminal
`complete/COMPLETE`. The fixed workload ran exactly 192 model requests with
zero retries and zero response errors, retained its result, restored production
and cleared every runtime control. Its preregistered development quality gate
returned `reject`; K2 must not proceed to sealed evaluation, shadow collection,
promotion or routing.

## Content-free measurement

- retained result SHA-256:
  `1aace7639319967dc72f51f7c973deb314944f047256a79c6ab1a3f1cb2eb709`;
- retained result bytes: 80,674;
- cases / model requests: 192 / 192;
- retries / response errors: 0 / 0;
- shortlist recall / raw exact: 179 / 140;
- accepted / accepted exact / accepted errors: 110 / 100 / 10;
- accepted error rate: 0.090909090909;
- unsafe false routes: 7;
- routed privacy underclassifications: 0;
- development gate: false / `reject`;
- sealed evaluation access: false;
- authority: not granted;
- automatic routing: off.

The accepted floor requires at least 116 accepted decisions and exactly zero
unsafe false routes. Both conditions fail. This is a candidate-quality reject,
not a workload or recovery failure.

## Evidence and restoration

The root-custodied attempt directory contains exactly five single-link,
root-owned mode-0600 regular files. The platform reconciler accepts the booking,
terminal, owner receipt and retained result as one complete transaction with
`production_restored=true` and matching result digest.

Independent checks confirm the lease ready; drain/operation state and locks
absent; no owner, guardian, K2 process, transient listener or port 11436
listener remaining; LXC104/110/116 running; Aster Agent, accepted
llama.cpp/SYCL and Speech active with zero recorded restarts; accepted model,
binary and unit pins unchanged; authenticated service probe successful; EPUB
and News schedules healthy; and `pvescheduler`, `pvestatd`, dispatcher and Lab
Hours Doctor healthy.

## Stop boundary

Do not invoke or retry this booking. Do not install the conditional sealed
two-host packet, open sealed inputs, register a sealed K2 effect, collect M5
shadow evidence or make an M6 promotion decision. Retain all K2 attempt and
rollback evidence. Stream A may continue offline successor selection; any new
B60 effect needs a distinct fixed workload and reservation.
