# D3 — corrected native first-case gate (build 11)

**Status: PREPARED LOCALLY; NOT APPROVED OR EXECUTED.** Owner: Jason.
This gate replaces only the failed pre-send build 10 attempt. It permits at
most one reviewed fictional question and no other live model turns.

## Why a new gate is required

[Build 10 stopped before Send](D3-native-build10-first-case-gate-2026-10-09.md):
the existing private journal directory made Foundation throw file-exists.
The local journal still has one historical request and turn, no evaluation
event file exists, and no evaluation request ID was stored. A different binary
must be installed before retrying. The fix treats only file-exists as an
expected condition, then verifies directory type, canonical path, ownership
and owner-only permissions. A repeat-call regression test passes. It does not
change the question, model, tool boundary, gateway or worker.

## Frozen candidate and baseline

- Installed build **10** executable SHA-256:
  `d7c9c98faa79cfa57b01ebcd2b05eebcee0c51776c05b0527791450a2ee76516`.
  It must not send a request; its journal precondition is broken.
- Preserved signed build **9** rollback executable SHA-256:
  `a284b7d2525698c982736d94baa624115dbce3fe72d275fd53dec0567beeddd2`
  at `/Applications/AsterCompanion.pre-evaluation-20261009.app`.
- Signed, unregistered build **11** candidate executable SHA-256:
  `95c8d0254eea14f8d75486c24da326f2c0b365e5e3c28da9ac409ae18e07f62c`.
  Strict signature verification passed. Changed journal-helper source SHA-256:
  `03991d7f89759e4682032dce96044489cc9cedf6f241eb6855f2264890e99741`.
  Evaluation UI source remains
  `40a7c150bea473aee6a520757bb79e180cf401b9f98beae0b08c3238305c7bc8`.
- The bundled metadata-only manifest remains
  `6063d71daf8ee917dcb95e5e6836d0bbdfd768df88870b14922da2b091ce285b`:
  ChatGPT sign-in, `gpt-5.6-luna` medium, no MCP, read-only sandbox, disabled
  web, one turn, no automatic retry. Preflight did not run inference.
- **47 native tests passed**, including repeat use of the private directory
  and rejection of a file at the expected directory path.
  The prior 297 Python tests remain the baseline; no Python source changed.

## Exact bounded action after approval

1. Recheck hashes, signature, manifest, journal count, absence of evaluation
   events/pending ID, Aster gateway closure, worker inactivity and Keychain
   state. Stop on drift. Preserve a verified whole-build-10 rollback copy;
   retain build 9 and all private journal files.
2. Quit build 10, install only signed build 11 at the same app path, register
   the existing URL scheme, and launch with
   `--aster-local-codex-evaluation`. No other local or remote service changes.
3. Jason reviews **case 1 only**: “What does HTTP status 503 mean? Answer
   briefly and distinguish it from proof of a lasting outage.” He checks the
   ChatGPT cloud-consent box and clicks Send once. Do not advance to case 2.
4. Verify one new local request maps to one Codex turn, the visible answer
   does not imply a lasting outage, and the private metadata-only log records
   submitted/completed and timings without question or answer. Recheck the
   closed gateway and inactive worker. A failure or uncertainty means stop,
   reconcile the original ID read-only, and do not resend.
5. Give Jason time to keep the volatile answer privately, close the flagged
   app, reopen normally, and verify signed-in Aster and hidden evaluation
   control. If the normal app regresses, restore verified build 9 or 10 only
   after diagnosing which is sound; never discard journals.

This gate needs explicit approval for **build 11 installation and one new
subscription-backed question**. It does not approve the other eleven cases,
arbitrary prompts, infrastructure tools, gateway activation, worker grants or
Git push. A single good answer establishes only a functioning first-case path.
