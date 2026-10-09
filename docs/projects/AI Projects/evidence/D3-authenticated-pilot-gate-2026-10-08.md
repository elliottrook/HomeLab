# D3 — one authenticated Aster/Codex result pilot

Status: APPROVED ATTEMPT FAILED AT STARTUP; ROLLBACK VERIFIED. Approval consumed.
The [corrected retry gate](D3-authenticated-pilot-retry-2026-10-08.md) now controls
the next action. The original frozen package and scope below remain provenance.

## Executed result

Jason approved the bounded pilot. Rechecked all disabled-package hashes, main
source, healthy 35-path baseline, inactive exact identity/bindings, unexpired
password, zero grants, three retained snapshots and unchanged worker fingerprint.
Installed the five approved members, public CA and private Aster-owned state
directory with the specified checkpoint. Syntax and systemd unit verification
passed. Reloaded and restarted Aster once.

Startup failed in `runtime.private_file` opening `gateway.lock` with OS error 30,
read-only filesystem. The deployment preflight missed the effective systemd
sandbox: `ProtectSystem=strict` with `ReadWritePaths` limited to
`/var/lib/aster/notifications`. Unix directory ownership alone was insufficient.
The existing unit automatically retried startup; no second manual pilot restart
was attempted. This is a deployment preparation defect, not model evidence.

Applied the authorized rollback: removed only the exact-hash pilot drop-in,
reloaded systemd and restarted Aster once. Independently verified active service,
health/Companion 200, pilot/owner delegation 404, all original 35 paths restored,
unchanged main application and absent runtime worker credential. Post-rollback
systemd reports zero restart count. The state directory contains only the approved
specification; no ledger, assignment, model call or worker activation occurred.
Authentik metadata independently confirms user still inactive and zero access or
refresh grants. Therefore there was nothing to revoke; credentials were not used.

Keep checkpoint, candidate modules, public CA and private specification. No
snapshot restore, source rollback, ledger deletion, credential renewal or push.
The corrected local drop-in adds only the missing private state-directory write
exception; another deployment/restart requires the new bounded approval.

## Outcome and boundary

Prove one fictional assignment can travel from the deployed Aster gateway to
the manually started Mac worker, through ChatGPT-authenticated Codex, and back
to Jason's authenticated Aster result page. This is connectivity evidence, not
sysadmin qualification, unattended deployment, voice integration or graduation.
There is no HTTP job-creation endpoint, scheduler, automatic replay, tool access,
personal context, live incident data, paid API fallback or permission expansion.

Use the existing fixed Orion exercise in `delegation/pilot.py`: a fictional
service returned 503 once and subsequently 200; explain known/unknown facts and
possible read-only checks without claiming to perform them. One model turn,
configured `gpt-5.6-luna`, medium reasoning, 180-second worker deadline. The model
choice is the installed configuration, not a recommendation or quality result.

## Verified preparation evidence

- Previous disabled deployment remains the accepted baseline, commit `2581796`.
- Installed Codex is now 0.162.0-alpha.2, binary SHA-256
  `cb4e4994627e770800a940b42969c77855a3fc09a6e60b02aa6319f670d6b6ab`.
  Metadata-only preparation confirms ChatGPT auth, configured model/reasoning,
  zero enabled MCP servers and disabled tools. A new offline fake-provider capture
  offered zero tools and no Authorization header; no real inference was made.
  Sandboxed metadata startup disconnected; host-runtime execution succeeded.
  This is a host-runtime restriction, not evidence of subscription failure.
- Primary contract: [Codex App Server](https://learn.chatgpt.com/docs/app-server).
  Installed executable and captured request are the evidence for this version.
- Live Authentik source resolves this provider's hashed-user subject to `user.uid`.
  Worker subject and existing Companion owner hash are pinned in the candidate.
- Live Companion uses `access_token` and millisecond `expires_at` browser storage;
  the result page reuses that session without exporting it or storing new tokens.
- Aster cannot read `/etc/homelab-broker/openbao-ca.crt`. A separate public CA copy
  is required; SHA-256 `86fa3b74acf9aff4df1cefd2aef54763d70d431fa0ee289ac9f3642ec3c5bf74`.
  `/etc/aster/openbao-ca.crt` is absent. `/var/lib/aster` is root-owned 0755, so
  provision the new private delegation subdirectory explicitly for Aster.
- Installed Authentik `providers/oauth2/views/introspection.py` checks grant
  expiry/revocation, not current user activity. Initial inference that deactivation
  was insufficient missed its post-save signal. The later
  [successful session result](D3-supervised-session-pilot-2026-10-08.md) verifies
  this version's deactivation hook removes user grants; explicit scoped cleanup
  and independent absence checks remain useful defense in depth.
- 237 local delegation tests passed. New coverage includes one-time admission,
  wrong approval/job refusal, private single-link ledger requirements, disabled
  credential checking, denied unauthenticated access, and distinguishing an
  authenticated missing job from an unmounted route. A Node VM browser-script
  check confirmed signed-out requests make no network call and returned markup
  is displayed as literal text. This is not a live browser acceptance result.

## Frozen artifacts

Archive `/private/tmp/aster-authenticated-pilot-20261008.tar`:
`6a840a059b7b2c488aa77ae76d030242347388a241f369343518b78b83a25888`.
Adjacent `aster-authenticated-pilot-20261008-manifest.json` records member hashes.
Reconstruct only identically from the committed candidate if temporary files vanish.

| Archive member | SHA-256 |
|---|---|
| aster-delegation-pilot.conf | 99339afea26caf6da6b5f150c1f7ea3fd8ffc0f5466b4327c1a33d3e226d9382 |
| delegation/deployment.py | 221bd433a5ffd531268dd08877ac4393ba531c182dfbae6ae1da11c458b426cc |
| delegation/pilot_admission.py | b3c9ebfc1a38994e04712640871dc016649ad354382c0b29599fa3bfcf05b0c7 |
| delegation/pilot_view.py | bd6cc7c20a4afefec8ed0cb35907fbeffb626d82b582ac0b7e251e962cf7557b |
| pilot-spec.json | c35ee6fe27ffc5fab1b9ff3cca40b1a516465f2ac2b3dc44c70ebd14aa1b6b05 |

Worker manifest `/private/tmp/aster-connected-prepared-20261008.json`:
`24f7afcfd9011267ab8b7521bec170d1f0b5f021984bb96b51591be6f4220888`.
It binds all delegation Python sources and the Codex binary, model and controls.
Any change requires re-preparation and review before a turn; never bypass mismatch.

Admission specification (metadata, no secrets):

```json
{
  "job_id": "orion-connected-20261008",
  "worker": "aster-codex-worker-mac",
  "request_sha256": "8ae1862acc26aa8f0303de8b49bef3acc0043076b1d6f5ae7c636ea386a4bad0",
  "scope_sha256": "c8650c8e07938bad8e130a06bcd6d9d869c5f9f0daf9b5a191959ed457b13c4e",
  "owner": "1bc78b70fa12fe11380d86700ee8bf360416296a09cbbb41e56618b168327f20",
  "model": "gpt-5.6-luna"
}
```

Canonical admission checksum:
`2eddc20ea62d2db9bb7de313a55ce1814bc2a59971b8bbaea227bd29764b0781`.
A checksum binds an operator-approved specification; it is not an independent
authorization mechanism and does not grant the model admission authority.

## One bounded approval requested

1. Recheck live app and installed disabled-package hashes against the previous
   gate/manifest, service health, absent pilot destinations/state, exact identity
   objects/bindings, credential lifetime, binary/manifest and snapshot presence.
   Password expiry is October 9, 2026 at 19:02 Vancouver. The AppRole SecretID
   also has a 24-hour issuance lifetime. Stop if expired; no renewal is included.
2. On LXC 104 create root-0700 checkpoint
   `/var/lib/aster-delegation-checkpoints/pilot-20261008`; preserve the old
   `deployment.py` and non-secret baseline. Verify exact hashes before replacing
   only that module; add `pilot_view.py` and `pilot_admission.py` root 0644.
   Preserve the live main application and all other existing modules/drop-ins.
3. Copy the verified public CA to the absent `/etc/aster/openbao-ca.crt` root
   0644. Create absent `/var/lib/aster/delegation` owned by existing Aster UID/GID,
   mode 0700. Store `pilot-spec.json` there owned by Aster mode 0600. Install the
   candidate `aster-delegation-pilot.conf` root 0644 in the service drop-in
   directory. It enables only delegation, pins worker identity/public CA, and
   delivers the existing encrypted AppRole through systemd. No plaintext export.
4. Validate syntax/unit, reload systemd, restart only Aster once. Expect a brief
   Aster/Companion interruption. Within 60 seconds require active service, existing
   health/Companion 200, unchanged original paths, added pilot routes, correct
   private ledger ownership/modes and delivered credential metadata only.
5. Activate only Authentik service user PK 11 `aster-codex-worker-mac`, after
   checking provider PK 51/client `aster-codex-worker` and prior exact policy
   bindings. No provider, scope, credential, other user or application changes.
6. Run local `pilot_connection_check.py --run` once. It privately uses only the
   named Keychain item and checks missing/malformed identity 401, valid worker
   access to the fixed nonexistent assignment 404 with `Job not found`. No
   credentials or response bodies are printed. It creates no job or model turn.
   This validates the complete custody/introspection path; it does not prove
   every cross-client denial. Prior source/fixture/canary evidence remains bounded.
7. As the Aster service user, invoke `pilot_admission.py --run` with the private
   specification and exact checksum above, once. It requires the existing private
   ledger and gives this job a 240-second admission window. Never delete/reset
   the ledger or change job ID to recover from uncertain admission/execution.
8. Run `connected_worker.py --run --job-id orion-connected-20261008` with the
   approved worker checksum and fresh private local evidence directory
   `.aster-local-state/connected-pilot-20261008`. One fixed fictional turn only;
   no auto-retry, alternative model or fallback billing. Do not print final answer,
   credentials, provider errors or hidden reasoning through operator tooling.
9. On completion OR failure disable that exact user, then mark AccessToken and
   RefreshToken grants with `user_id=11, provider_id=51` revoked. Verify inactivity
   and zero nonrevoked matching grants by counts only; retain grant audit records.
   No other credentials are rotated/deleted. If cleanup fails, stop the worker,
   invoke the gateway rollback below and report cleanup unconfirmed.
10. On success leave the owner-readable gateway running so Jason can view the
    in-memory answer at `https://aster.elliottrook.com/companion/codex-pilot`, using
    his existing Companion sign-in. No enabled worker or new job is left running.
    User visibility is an outstanding acceptance gate until actually checked.
    Confirm existing health, record sanitized status/timing/usage, and commit
    locally. No Git push is included.

## Failure, rollback and limitations

On failure remove only the exact new pilot drop-in, reload and restart Aster once
to return to the accepted disabled wrapper. Preserve the ledger and checkpoints;
do not restore snapshots, erase uncertain work or recreate the assignment. If
needed restore only the exact backed-up `deployment.py` as part of that rollback.
Verify health/Companion and delegation 404. Leave inactive candidate files/public
CA for provenance. Do not toggle the global AI-PAM kill switch: other consumers
must remain independent. Account deactivation and targeted grant revocation above
are included on both success and failure.

If interrupted, first inspect ledger, worker state and identity metadata; perform
approved cleanup before considering any new test. Do not infer successful model
cancellation from transport/process disappearance. Tokens have at most five-minute
lifetimes, but that is not a substitute for verified revocation or cancellation.

Results are currently ephemeral on Aster; a gateway restart can require answer
recovery, never resubmission. The page provides refresh/stop controls and is not
yet the normal chat/voice flow. Existing successful and failed cancellation
evidence remains unchanged. One success cannot graduate D3: owner visibility,
follow-up/reconnect, operational support and remaining reliability gates persist.

No new hardware, network/firewall/DNS rules, daemon, scheduled task, NetBox record,
Homepage link, backup policy or wiki claim of a production feature is justified
by this pilot. Existing snapshots/checkpoints protect recovery. Record deployment
facts after execution; monitoring graduation remains future work.

Approval is required by repository `AGENTS.md`'s immediate remote-write rule and
the project's connected-pilot gate because this changes a live service, activates
an identity and submits a cloud turn. Local preparation does not authorize them.
