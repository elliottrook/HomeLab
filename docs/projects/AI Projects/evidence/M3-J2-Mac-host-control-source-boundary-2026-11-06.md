# M3 J2 Mac host-control source boundary — 2026-11-06

## Decision

The admitted J2 transaction is a Mac-local, portable-Python, single-thread CPU
workload. It does not call, drain, schedule against or otherwise compete with
the B60 local-AI stack. Under the repository's clarified reservation boundary,
it therefore requires the reviewed Mac host controls below rather than an
Aster Lab Hours booking. No worker was started by this review.

## Fixed workload and host

- host: `Jasons-Mac-mini.local`;
- hardware: Mac mini `Mac16,10`, Apple M4, ten cores, 16 GB memory;
- operating system: macOS 26.6.2 build 25G83;
- transaction source SHA-256:
  `e9f8821b4316197b25cfac3c33a949128317002249da9f6b2cc4e0169e0435c8`;
- Mac owner source SHA-256:
  `ca9af007576a072adc47c82bd7cfa9d7794308c6cebd3c1da643bd106285f40b`;
- exact corpus, release, admission and recipe pins remain those in the
  transaction source evidence;
- backend: portable Python CPU reference, one thread, no accelerator, network,
  route, tool, deployment or sealed-evaluation access.

## Runtime controls

`nlu_j2_mac_host_owner_v1.py` fails closed unless all of these pass:

1. all four input files and the transaction source are regular, non-symlink
   files matching exact compiled SHA-256 pins;
2. both `/private/tmp/aster-mac-ai-exclusive.lock` and
   `/private/tmp/aster-j2-training.lock` are acquired with no-follow,
   nonblocking exclusive locks;
3. the fixed J2/J1/MLX competing-process set is absent before and after lock;
4. available memory is at least 2 GiB and swap does not change between the
   initial and locked admission observations;
5. memory and swap are re-observed every five seconds; available memory below
   2 GiB or swap growth above 256 MiB terminates the complete process group;
6. the hard deadline is two hours, followed by TERM and a ten-second grace,
   then KILL if required;
7. completion requires exit zero, no stderr, the exact six-file output set,
   inert authority/routing/deployment values and no remaining worker process.

The workflow stops no Mac service, so restoration requires zero stopped
services plus terminated worker state and released locks. The underlying
transaction retains bounded create-only failure evidence on an uncertain or
failed run; the same output path cannot be retried.

## Fresh measurements and estimate

The read-only host preflight measured:

- available bytes: `3016982528`;
- swap used bytes: `0`;
- competing fixed processes: `0`;
- root/data free space: approximately 174 GiB;
- load averages: 2.27 / 2.21 / 2.71 at observation time.

One real admitted-row forward/backward gradient calculation against the frozen
initial tensors completed in 0.049 seconds. The transaction performs 30,720
training rows plus 7,680 after-epoch validation forwards and two final 192-row
replays. Allowing for optimizer, serialization, process and host-load overhead,
the operational estimate is 35–55 minutes. The two-hour owner timeout is a
conservative hard ceiling, not a schedule.

The model has 46,848 parameters. Forty binary64 checkpoints are 14,991,360
bytes before Python object overhead, leaving substantial margin above the
2 GiB fail-closed floor.

## Validation and remaining gate

- Mac host-owner focused tests: 4/4;
- content-free input-stage focused test: 1/1;
- full J2 suite: 121/121;
- live read-only Mac resource/process preflight: pass;
- `git diff --check`: pass.

The exact content-free inputs are now staged create-only at
`/Users/jelliott/lab/private-benchmarks/aster-stream-a/j2-training-inputs-20261106`
under a mode-0700 directory with three mode-0600 files. Their stage receipt is
`00b4dc70c9a0e869c3cce4d05c6bd54930428427e3d4eccd6ff7c0aa73d9fc26`.
The compiled Mac owner accepts all real input/workload pins, and the proposed
first result path
`/Users/jelliott/lab/private-benchmarks/aster-stream-a/j2-training-result-20261106-r1`
is absent. Input staging did not start training.

The remaining gate is an exact owner training-effect decision for one run of
this hash-pinned Mac owner against the retained admitted inputs and a new
create-only output directory. Approval would authorize only candidate training
and content-free validation/replay evidence. It would not authorize sealed
evaluation access, B60 use, deployment, routing, tools, promotion, service
restart or an automatic retry.
