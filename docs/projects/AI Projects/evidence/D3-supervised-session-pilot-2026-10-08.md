# D3 — one supervised credential session

Status: APPROVED PILOT COMPLETED; CLEANUP VERIFIED; OWNER DISPLAY CHECK PENDING.
Approval consumed. No unattended promotion or Git push.

## Executed result

Jason approved. Local candidate commit `644af8a` was saved before execution.
Fresh metadata matched the exact fingerprint; disabled live baseline and empty
ledger, installed source hashes, original app/CA/specification and inactive exact
identity/bindings were verified. Reinstalled only the corrected drop-in; strict
sandbox and two exact write paths remained. One restart succeeded, preserving
all 35 original routes and returning healthy Companion/pilot pages.

Activated only the worker, admitted `orion-connected-20261008` once, and ran the
new worker once. It returned `state=completed, automatic_retry=false`. This code
path requires supervised bootstrap, the missing/malformed/valid identity checks,
one assigned model turn, terminal receipt, answer delivery and usage delivery.
Independent read-only gateway ledger inspection found exactly one completed job,
its answer digest, usage and no cancellation request. No second inference or
diagnostic repetition occurred. The full answer was not read into operator tools.

Provider-reported usage snapshots (last and total equal): 7,882 input tokens,
4,864 cached input, 232 output, 0 reported reasoning-output tokens, 8,114 total.
Configured reasoning was medium; zero reported reasoning tokens is not evidence
that the setting was disabled. These counters are not a monetary invoice or
subscription-capacity measurement. Authentication remained ChatGPT; no PAYG
fallback. The overall process returned after roughly 16 seconds of tool wait,
not an isolated model latency benchmark.

Disabled the exact worker immediately. Cleanup's explicit grant update affected
zero rows; independent broader metadata found no access grants for provider 51
or user 11 and no provider refresh grants. Source inspection explains this:
`/authentik/providers/oauth2/signals.py` post-save `user_deactivated` deletes the
user's access, refresh and device grants (including expired) unless cleanup is
inhibited. The user deactivation had already removed them. This corrects the
earlier inference from introspection code alone that deactivation was insufficient
on this installed version. No tokens or secret values were inspected. Dedicated
identity isolation matters because this built-in hook applies to all its grants.

Aster remains active; health, Companion and pilot page return 200; main source
hash is unchanged. Gateway stays enabled for the owner to read its in-memory
answer, with worker inactive, no scheduler/new job and no live token. Do not
restart it merely for cleanup; that would discard the answer. No rollback needed.
Private local evidence is `.aster-local-state/supervised-session-pilot-20261008`.
Checkpoint/ledger retained. Remote Git synchronization remains pending approval.

Owner acceptance still requires Jason to open
`https://aster.elliottrook.com/companion/codex-pilot` in his usual signed-in browser
and confirm the fictional Orion answer is visible. The app browser-open request
was queued, not evidence of display or successful login. No user token is requested
or copied. Follow-up/recovery/normal chat/voice and unattended operation remain
unproven; this does not graduate D3 or authorize live sysadmin work.

## Candidate and evidence

242 delegation tests pass. WorkerSession bootstraps once, allowing 90 seconds for
the exact Keychain Allow prompt. WorkerToken exchanges the password once, retains
no password as session state, and returns a token with a conservative monotonic
deadline measured before exchange minus ten seconds. Session requires 200–300
seconds remaining, holds only the token in memory, refuses repeated bootstrap or
automatic renewal after expiry/failure, and drops its token reference on close.
Python memory is not claimed to be cryptographically erased. Every gateway
request still performs broker and online introspection checks. Tests confirm
reused tokens cannot bypass gateway denial. Fixed stage labels now distinguish
Keychain, token exchange/validation, gateway check and assigned turn failures
without printing secret-bearing exception text.

The installed gateway modules remain unchanged, including its existing
credentials.py. The local Mac credential/session changes are not deployed there.
Metadata-only preparation confirms ChatGPT auth, gpt-5.6-luna/medium, tools off,
and unchanged Codex binary hash
`cb4e4994627e770800a940b42969c77855a3fc09a6e60b02aa6319f670d6b6ab`.

Prepared worker manifest `/private/tmp/aster-supervised-session-prepared-20261008.json`:
`41d4e7eeb4bc47e3548eaeb43fcb40d1d9482c1f44d04e8d81aee2131437b485`.
Corrected drop-in remains
`3dc2e807b5bf5e509ed54e02c04d2641260e82059a01fd415c28775f6c9368b5`.
Admission checksum remains
`2eddc20ea62d2db9bb7de313a55ce1814bc2a59971b8bbaea227bd29764b0781`.
Job: `orion-connected-20261008`, only if existing ledger independently shows
no assignment. No ledger reset, job replacement or uncertain execution replay.

## Approved operation and recovery

1. Verify healthy disabled baseline, retained installed hashes/CA/specification,
   private empty ledger, exact inactive identity/bindings, zero grants, credential
   lifetime and unchanged worker fingerprint. Password expires October 9 at 19:02
   Vancouver; AppRole retains its original 24-hour lifetime. No renewal included.
2. Reinstall only the corrected drop-in, preserving ProtectSystem=strict and the
   notifications plus private delegation directory write exceptions. Validate,
   reload and restart Aster once. Verify health, original 35 paths, pilot routes,
   private ledger and runtime credential metadata. No gateway source overwrite.
3. Activate only user 11/provider 51 with existing exact bindings. Admit the one
   fixed fictional Orion specification as Aster using the checksum above. This
   reserves the job before bootstrap so the connection check and turn can share
   one token in one private process. Admission does not execute a model. If
   bootstrap fails, retain the unoffered job; never automatically resubmit it.
4. Run connected_worker once with the new fingerprint, fixed job and fresh private
   `.aster-local-state/supervised-session-pilot-20261008` directory. Jason enters
   his login Keychain password in the named OS dialog and selects Allow once.
   No Always Allow/ACL changes. In that process, bootstrap and the existing
   credential-path check must pass before job offer/model-agent creation.
   One fictional turn, 180-second model deadline, no tools, personal data, PAYG
   or auto-retry. Do not separately rerun the credential check or private read.
5. On completion or failure disable exact user 11 and revoke only its provider-51
   access/refresh grants. Verify inactivity and zero nonrevoked grants by counts.
   On success preserve the owner-readable result page for Jason's acceptance.
   Health and sanitized status/usage must be checked; no assumed owner visibility.
6. On failure remove only the exact corrected drop-in, reload and restart once
   into the proven disabled configuration. Preserve ledger/checkpoints/evidence;
   no snapshots restored, global broker switch changes or resubmission. If
   interrupted, reconcile worker/ledger/identity first. Process disappearance is
   not proof of model cancellation. Stop if cleanup/rollback cannot be verified.

The earlier [startup and credential failures](D3-authenticated-pilot-retry-2026-10-08.md)
remain evidence. This pilot cannot establish unattended credential availability,
general sysadmin quality or D3 graduation. Owner visibility, follow-up/reconnect,
operational support and cancellation limits remain separate acceptance gates.
