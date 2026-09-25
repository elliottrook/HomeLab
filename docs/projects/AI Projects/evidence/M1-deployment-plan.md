# M1 deployment preparation — staged corrective release

Date: 2026-09-25. **PROPOSAL, not authorization or deployment.** Core candidate `39221b7`; revised transport preserves the subsequently deployed M6 gateway and adds only authenticated caller binding. See `M1-stage1-manifest.json` for exact staged artifacts. Read-only discovery followed the local checkpoint; no production file, service, identity, database row, policy or credential was changed by this task.

## Verified current state

Direct read-only SSH to Proxmox `192.168.50.10`, projecting only named non-secret fields:

- LXC 104: `aster-agent`, `homelab-broker`, `homelab-broker-approval` active/running. Broker and approval run as `hlabroker`; Companion runs as `aster`. Agent socket `/run/homelab-broker/mcp.sock`; approval socket `/run/homelab-broker/approval.sock`; Forgejo read gateway `/run/homelab-forgejo-mcp/gateway.sock`.
- Broker database `/var/lib/homelab-broker/broker.db`: integrity `ok`; 7 consumed, 1 denied, 6 expired, 1 revoked; **zero pending/approved at observation time**. Approximately 14.69 GB filesystem free. **Later post-M6 observation supersedes the request count:** 8 consumed, 1 denied, 6 expired, 1 pending, 1 revoked. The pending request is owned by the AI-PAM workflow; do not consume, approve or revoke it here. This is not a reservation; recheck immediately before applying.
- Core/transport/approval source files are root:root mode 0644; DB UID/GID 996:986 mode 0600. Preserve owners/modes.
- Authentik LXC 106 runs `ghcr.io/goauthentik/server:2026.8.0`. Provider 26, `aster-companion`, public client, authorization-code/refresh grants, hashed-user-ID subject, per-provider issuer. Application has one enabled non-negated direct binding to active user `jason`; no group/policy binding was returned for that application.
- Flow `aster-companion-passwordless`: identification at order 10, WebAuthn validation at 20, login at 100. Identification has email/username fields and no password/WebAuthn/passwordless shortcuts. Validation permits only WebAuthn, requires user verification, denies unconfigured users and has zero reuse threshold.
- Four provider property mappings (openid/profile/email/offline_access) contain no ACR/AMR reference. Installed ID-token code defaults ACR to `goauthentik.io/providers/oauth2/default`; it is not passkey-specific. The implementation emits AMR `user` for the distinct `auth_webauthn_pwl` method and generic `mfa` when an MFA device is recorded. The ten most recent owner login-method projections contain eight `auth_mfa` and two `password`, not `auth_webauthn_pwl`. These are owner-wide method projections, not token samples or a proof of any particular Companion session.
- Candidate subject hash was derived source-locally from the selected provider's subject algorithm and issuer for `jason`; no subject, credential, token or login session was exported. The candidate hash is not activated or published in Git. Stage 1 does not require it.
- **Baseline changed during preparation:** AI-PAM initially reported M6 not deployed, then reported its separately authorized deployment had completed. Direct re-verification confirms the active write gateway, updated transport/command line and unchanged core/approval service. The obsolete draft was withdrawn before any deployment. No M6 gateway, unit, grant or custody file is a deployment target here.

Live SHA-256 observations:

| File | SHA-256 |
|---|---|
| `/opt/homelab-broker/broker_core.py` | `c8f95571ab5b7be1783fe54394047a8d5c40d9cc9121ffcbdc7ad1af99a87cb1` |
| `/opt/homelab-broker/broker_service.py` | `cb52ca372b9af8f4abefc6b5ef3ac55655482e7f537773e45d90ccd2ab068eec` |
| `/opt/homelab-broker/broker_approval_service.py` | `a73625fa3b68fe3a5e65f8960b6c96d9fec8fbf4c9dbdc75fe4136a5625c50d8` |
| `/opt/aster-agent/aster_agent.py` | `8777687ce97055d2db3254aa6b30ddf37fc61e73dac2bd18008cbea3fef1a8b6` |
| `/opt/aster-agent/broker_approvals.py` | `3e376175640d7da84ab4e47b5bbc5e06075e0ce477283df2ae979e8ed44b1b0c` |

The revised transport was taken from the AI-PAM worktree only after its SHA-256 matched the deployed `cb52ca…` source. Its separate `forgejo_write_socket` constructor/CLI argument and existing Yellow dispatch are preserved. The only difference from that deployed source is passing authenticated `agent_id` into consume. This does not grant or newly enable the write capability. M6 gateway implementation/credentials remain owned by the separate project.

The M6 transport regression was retained, and an additional socket-level test proves pending, wrong-caller, demoted, changed-payload and replay denials do not reach either fake gateway. The combined local broker suite passes **57 tests**. The retained old approval service passes synthetic Yellow/Red compatibility including stale-Red, wrong-caller and replay denial via `verify_legacy_approval.py`. No real repository write was attempted.

The `39221b7` transport must **not** be deployed verbatim: it predates M6 and lacks the now-required CLI parameter. Only the revised manifest is eligible.

## Decision: split deployment, retain the full M1 gate

The candidate's empty ACR allowlist is appropriately restrictive, but installing the full approval bridge now would disable Red/management workflows without an established replacement assurance path. **Do not map generic ACR, generic MFA, a recent timestamp or flow selection to passkey assurance.** The current owner-only application binding reduces the immediate non-owner exposure but does not replace explicit approver policy.

Stage 1 is a narrower corrective deployment of two files only. It leaves the old approval bridge/socket protocol intact and does not claim to solve the separate assurance/entitlement problem. This is a deliberate, reviewable split from the earlier all-at-once proposal. A local compatibility probe loaded the unchanged approval service from baseline `d954ae4` against the new core: pending listing, Yellow approval and identity-bound consume passed using synthetic data. No target action ran.

Stage 2 remains blocked on a properly evidenced assurance design and fresh end-to-end login test. M1 remains open after Stage 1. No broadened AI tools, autonomy or writes may rely on a completed M1 gate.

## Stage 1 — exact bounded approval scope

**Target:** existing LXC 104 only. **Artifacts:** the core from `39221b7` plus the M6-compatible transport, checked against `M1-stage1-manifest.json`. Replace their namesakes under `/opt/homelab-broker/` only. Restart **only** `homelab-broker.service` and `homelab-broker-approval.service`, because both import the core. Do not restart Aster, Forgejo gateway, Authentik, OpenBao or any guest.

**Permitted effects:** protected recovery checkpoint; brief broker/approval interruption; additive `requests.policy_hash` migration; invalidation of any unbound legacy pending work; synthetic offline validation on the guest; fixed read-only health/catalogue checks after restart. No network/DNS/firewall, group, grant, credential, model, target-service or systemd-unit changes. No approval-service or Companion source replacement in this stage.

### Ordered procedure and abort gates

1. Recheck AI-PAM owner activity and five live hashes. Abort on new source/runtime drift, M6 deployment in progress, pending requests, in-flight operations or uncertainty. Confirm the already deployed M6 write gateway and unit command line match the re-baseline; abort on further change. Do not race another task.
2. Stage only the two pinned source files plus their manifest in a root-only temporary release directory. Verify SHA-256, syntax, and Python compatibility before stopping anything. Staging is included in the requested deployment, not already performed.
3. Check free space and create a timestamped root-only checkpoint directory under `/var/lib/homelab-broker/rollback/`. Stop approval and broker services gracefully; verify inactive states. A stop must not kill an uncertain target operation—abort/reconcile first if any operation is in flight.
4. With both writers stopped, use SQLite's backup API to capture the database; preserve mode 0600. Retain original two source files and non-secret file metadata. Validate database integrity and a second disposable restored copy; retain terminal request counts and source hashes without printing payload/display/audit actor contents. Do not copy OpenBao custody or credentials.
5. Install the two files root:root 0644. Run schema migration once as `hlabroker` with both daemons stopped. Verify DB integrity and preserved terminal-state counts. Legacy pending/approved authorizations, if unexpectedly present, are an abort condition from step 1; never backfill a policy hash.
6. Run the Stage 1 subset (37 tests: `test_broker_core`, `test_broker_service`, `test_adaptive_foundation_regressions`) against isolated temporary databases/fake sockets, plus `verify_legacy_approval.py --approval-service /opt/homelab-broker/broker_approval_service.py` from the staged candidate directory. The full new-approval suite is a Stage 2 candidate check, not a claim that those new controls are live. No fixture principal/capability is added to the production DB.
7. Start broker and approval services; verify active states, both Unix socket owners/modes, database integrity, and new hashes. Check broker health/catalogue through an existing registered identity without creating or consuming a production request. Verify approval socket rejects an unauthorized peer; confirm the unchanged Companion endpoint rejects unauthenticated HTTP.
8. Observe a bounded 10-minute window for service restarts, lock failures, errors and heartbeat/socket availability. Collect only selected status/counters, not unfiltered secret-bearing logs. This window is an initial operational check, not long-term graduation.
9. Record evidence and update current-state documentation. Stop at the Stage 2 gate; do not enable a write capability, change approver configuration or push Git without the separate authorization for that action.

### Recovery

Before step 5, failed checkpoints or validation mean leave existing files unchanged and restart the original services if safe. After activation, stop the two broker services if authorization behavior, migration or health fails. Preserve the failed DB/source for diagnosis and keep human SSH administration available. **Do not restart old core code against broadly granted production state.** A rollback that restores the old source must keep broker/approval services disabled until a corrected restrictive candidate is ready. Do not restore an older database and reopen access: stale authorizations could be resurrected. Target-side state and completed effects are never rolled back by a DB restore.

Expected user impact is a short interruption to AI-PAM broker/approval calls; Aster chat and household functions are not restarted. If the candidate fails, AI-PAM may remain deliberately unavailable pending repair. Jason must accept that bounded availability tradeoff before deployment.

## Stage 2 — explicit identity and assurance gate

Prepare a separate bounded amendment for either a provider-specific, session-derived passkey claim or a verified dedicated passkey step-up flow. Do not create a constant assurance claim. Prove that password/TOTP/generic MFA, stale sessions, refresh and malformed/missing claims cannot acquire fresh passkey assurance. Validate a fresh real Jason session source-locally, exposing only boolean results and claim names/approved class, never bearer tokens. Confirm existing non-owner application denial and the derived subject hash before configuring the two allowlists.

The installed flow currently produces a generic method classification despite WebAuthn-only validation. A source-backed design can inspect typed authentication evidence, but user/device attributes or assumed application entry paths are not sufficient. Any provider mapping/flow modification needs its own exact checkpoint, tests, review and approval. Current evidence does not justify enabling `ASTER_BROKER_PASSKEY_ACRS`.

## Sources and research record

Installed Authentik 2026.8 source inspected read-only: `providers/oauth2/id_token.py`, `common/oauth/constants.py`, `stages/authenticator_validate/stage.py`; source behavior above is specific to that installed version. ORM projections used read-only PostgreSQL transactions and explicit fields; no provider secrets or session/token tables were queried.

Official references accessed 2026-09-25: [OAuth2 provider](https://docs.goauthentik.io/add-secure-apps/providers/oauth2) describes per-provider issuers and scope mappings; [WebAuthn stage](https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_webauthn/) distinguishes device setup from requiring WebAuthn during authentication. These docs do not prove this installation emits a passkey-specific claim; the live/source observations determine that conclusion.

## Prepared local release

`/private/tmp/aster-m1-stage1-20260925` contains the two installable source files, three synthetic test modules, the retained-approval compatibility verifier and the exact manifest. The staged copy passed all 37 Stage 1 tests and both Yellow/Red compatibility fixtures. It contains no database, credentials, live grants or personal request content. Reconstruct it from the committed files and manifest if temporary storage is cleared. Deployment approval and AI-PAM quiescence are still required.
