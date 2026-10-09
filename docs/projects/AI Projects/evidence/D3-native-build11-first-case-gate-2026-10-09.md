# D3 — corrected native first-case gate (build 11)

**Status: APPROVED AND COMPLETED FOR CASE 1 ONLY.** Owner: Jason.
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

## Observed first-case result — 2026-10-09

Jason approved build 11 and the same single fictional question. Before
installation, the installed build 10, preserved build 9 and candidate build 11
matched their pinned executable hashes; signatures passed. The prior local
journal still held one request and turn, with no evaluation event file or
pending evaluation ID. Aster was active with 44 API paths, GET-only on the
delegation jobs collection, two historical gateway jobs, and an inactive
Authentik worker with zero unrevoked access/refresh grants. A whole-build-10
rollback was preserved at `/Applications/AsterCompanion.pre-build11-20261009.app`
and verified before replacement. Build 11 installed with the pinned executable
hash and valid strict signature.

The signed-in normal Aster UI and the exact case 1 review appeared. The
metadata-only preflight passed. Jason reviewed the question and selected the
consent/send control. One new local request completed with one nonempty thread
ID, one nonempty turn ID and one usage record. The visible answer correctly
described 503 as service unavailable and explicitly rejected an inference of a
lasting outage. The UI reported **2.3 seconds** for the Codex turn and **3.0
seconds** send-to-result; the private event file recorded 2.273 and 3.044
seconds respectively. Its mode is 0600 and it contains only submitted and
completed events for case index 0, request ID, pinned manifest, timestamps and
timings—no prompt or answer. The pending ID remains recorded, and the next
case has not been selected. After the turn, Aster still had 44 paths, GET-only
job listing and two gateway jobs; the worker remained inactive with zero
unrevoked grants.

Jason approved closing the volatile answer. Companion exited cleanly and
reopened without the evaluation flag. Its signed-in normal Aster view was
visible; the local evaluation control was hidden, ordinary Ask Codex intake
remained disabled, and the installed build 11 executable hash and strict
signature still matched. The private journal retained exactly two local jobs
and two usage records total (one historical plus this case); the event file
still contained only submitted/completed for case 0. No next-case index was
stored. Aster still exposed 44 paths, GET-only on the delegation collection,
and two gateway jobs. This one case is a transport/measurement success, not a
reliability sample, router validation or sysadmin qualification. The other
eleven cases remain unapproved.
